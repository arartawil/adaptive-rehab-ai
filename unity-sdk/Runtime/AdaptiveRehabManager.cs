using System;
using System.Threading.Tasks;
using UnityEngine;

namespace AdaptRehab
{
    /// <summary>
    /// Unity MonoBehaviour wrapper for AdaptRehabClient
    /// Handles lifecycle and provides Unity-friendly async/await
    /// </summary>
    public class AdaptiveRehabManager : MonoBehaviour
    {
        [Header("Server Configuration")]
        [Tooltip("Server host address")]
        public string serverHost = "localhost";
        
        [Tooltip("Server port")]
        public int serverPort = 8000;

        [Header("Session Configuration")]
        [Tooltip("Unique session ID (auto-generated if empty)")]
        public string sessionId;
        
        [Tooltip("AI module to use")]
        public AIModule aiModule = AIModule.RuleBased;

        [Tooltip("Patient/User ID")]
        public string patientId = "unity_user";

        [Tooltip("Initial difficulty (0-1)")]
        [Range(0f, 1f)]
        public float initialDifficulty = 0.5f;

        [Header("Status")]
        [SerializeField] private bool isConnected;
        [SerializeField] private bool isInitialized;
        [SerializeField] private float currentDifficulty;
        [SerializeField] private string lastDecisionAction;
        [SerializeField] private float lastDecisionConfidence;

        private AdaptRehabClient client;
        private AdaptationDecision lastDecision;

        public enum AIModule
        {
            RuleBased,
            FuzzyLogic,
            ReinforcementLearning
        }

        // Events
        public event Action<AdaptationDecision> OnAdaptationReceived;
        public event Action OnSessionInitialized;
        public event Action OnSessionEnded;

        // Properties
        public bool IsConnected => isConnected;
        public bool IsInitialized => isInitialized;
        public float CurrentDifficulty => currentDifficulty;
        public AdaptationDecision LastDecision => lastDecision;

        private void Awake()
        {
            if (string.IsNullOrEmpty(sessionId))
            {
                sessionId = $"unity_{Guid.NewGuid().ToString().Substring(0, 8)}";
            }

            currentDifficulty = initialDifficulty;
        }

        private async void Start()
        {
            await InitializeAsync();
        }

        /// <summary>
        /// Initialize connection and session
        /// </summary>
        public async Task<bool> InitializeAsync()
        {
            try
            {
                Debug.Log($"[AdaptiveRehabManager] Initializing with session ID: {sessionId}");

                // Create client
                client = new AdaptRehabClient(serverHost, serverPort);

                // Check server connection
                isConnected = await client.PingServerAsync();
                if (!isConnected)
                {
                    Debug.LogError($"[AdaptiveRehabManager] Cannot connect to server at {serverHost}:{serverPort}");
                    return false;
                }

                Debug.Log("[AdaptiveRehabManager] Server connected");

                // Initialize session
                var profile = new PatientProfile(patientId)
                {
                    BaselinePerformance = 0.5f
                };

                var config = new TaskConfig("unity_vr_game")
                {
                    InitialDifficulty = initialDifficulty
                };

                string moduleName = aiModule switch
                {
                    AIModule.RuleBased => "rule_based",
                    AIModule.FuzzyLogic => "fuzzy_logic",
                    AIModule.ReinforcementLearning => "reinforcement_learning",
                    _ => "rule_based"
                };

                isInitialized = await client.InitSessionAsync(sessionId, moduleName, profile, config);

                if (isInitialized)
                {
                    Debug.Log($"[AdaptiveRehabManager] Session initialized with {aiModule} module");
                    OnSessionInitialized?.Invoke();
                }

                return isInitialized;
            }
            catch (Exception ex)
            {
                Debug.LogError($"[AdaptiveRehabManager] Initialization error: {ex.Message}");
                return false;
            }
        }

        /// <summary>
        /// Request adaptation decision
        /// </summary>
        /// <param name="accuracy">Performance accuracy (0-1)</param>
        /// <param name="speed">Performance speed (optional)</param>
        /// <param name="additionalMetrics">Additional performance metrics</param>
        public async Task<AdaptationDecision> RequestAdaptationAsync(
            float accuracy,
            float speed = 1.0f,
            System.Collections.Generic.Dictionary<string, float> additionalMetrics = null)
        {
            if (!isInitialized)
            {
                Debug.LogWarning("[AdaptiveRehabManager] Session not initialized");
                return null;
            }

            var state = new StateVector
            {
                PerformanceMetrics = new System.Collections.Generic.Dictionary<string, float>
                {
                    ["accuracy"] = Mathf.Clamp01(accuracy),
                    ["speed"] = speed
                },
                SensorData = new System.Collections.Generic.Dictionary<string, float>(),
                TaskState = new System.Collections.Generic.Dictionary<string, object>
                {
                    ["difficulty"] = currentDifficulty,
                    ["round"] = Time.frameCount
                },
                SessionId = sessionId,
                Timestamp = Time.time
            };

            // Add additional metrics
            if (additionalMetrics != null)
            {
                foreach (var kvp in additionalMetrics)
                {
                    state.PerformanceMetrics[kvp.Key] = kvp.Value;
                }
            }

            lastDecision = await client.GetAdaptationAsync(state);

            if (lastDecision != null)
            {
                // Update difficulty
                float difficultyChange = lastDecision.GetDifficultyChange();
                currentDifficulty = Mathf.Clamp01(currentDifficulty + difficultyChange);

                // Update debug info
                lastDecisionAction = lastDecision.Action.ToString();
                lastDecisionConfidence = lastDecision.Confidence;

                Debug.Log($"[AdaptiveRehabManager] Action: {lastDecision.Action}, " +
                         $"Difficulty: {currentDifficulty:F2}, " +
                         $"Confidence: {lastDecision.Confidence:F2}");

                OnAdaptationReceived?.Invoke(lastDecision);
            }

            return lastDecision;
        }

        /// <summary>
        /// Manually set difficulty (useful for testing)
        /// </summary>
        public void SetDifficulty(float difficulty)
        {
            currentDifficulty = Mathf.Clamp01(difficulty);
        }

        private async void OnDestroy()
        {
            if (client != null && isInitialized)
            {
                await client.EndSessionAsync();
                OnSessionEnded?.Invoke();
            }

            client?.Dispose();
        }

        private async void OnApplicationQuit()
        {
            if (client != null && isInitialized)
            {
                await client.EndSessionAsync();
            }
        }
    }
}
