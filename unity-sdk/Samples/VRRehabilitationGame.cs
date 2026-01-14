using UnityEngine;
using UnityEngine.UI;
using UnityEngine.XR;
using System.Collections.Generic;
using AdaptRehab;

/// <summary>
/// VR Rehabilitation Game: Reach and grab targets with hand controllers
/// Difficulty adapts based on accuracy, speed, and reach distance
/// </summary>
public class VRRehabilitationGame : MonoBehaviour
{
    [Header("VR Configuration")]
    public Transform leftHandController;
    public Transform rightHandController;
    public float grabDistance = 0.2f;

    [Header("Game Objects")]
    public GameObject targetPrefab;
    public Transform playArea;
    public Text scoreText;
    public Text instructionsText;

    [Header("Rehabilitation Settings")]
    public int targetsPerExercise = 10;
    public float exerciseDuration = 60f;
    public bool requireBothHands = false;

    [Header("Difficulty Scaling")]
    [Tooltip("Spawn distance range based on difficulty")]
    public Vector2 spawnDistanceRange = new Vector2(0.5f, 2.0f);
    
    [Tooltip("Target size range based on difficulty")]
    public Vector2 targetSizeRange = new Vector2(0.3f, 0.1f);

    private AdaptiveRehabManager rehabManager;
    private List<RehabTarget> activeTargets = new List<RehabTarget>();
    private int currentExercise;
    private float exerciseStartTime;
    private bool exerciseActive;

    // Performance metrics
    private int totalReaches;
    private int successfulReaches;
    private List<float> reachTimes = new List<float>();
    private List<float> reachDistances = new List<float>();

    void Start()
    {
        // Setup AdaptiveRehabManager
        rehabManager = FindObjectOfType<AdaptiveRehabManager>();
        if (rehabManager == null)
        {
            GameObject managerObj = new GameObject("AdaptiveRehabManager");
            rehabManager = managerObj.AddComponent<AdaptiveRehabManager>();
            rehabManager.aiModule = AdaptiveRehabManager.AIModule.ReinforcementLearning; // Use RL for personalization
        }

        rehabManager.OnSessionInitialized += StartExercise;
        rehabManager.OnAdaptationReceived += OnAdaptationReceived;

        // Find VR controllers if not assigned
        if (leftHandController == null || rightHandController == null)
        {
            FindVRControllers();
        }
    }

    void FindVRControllers()
    {
        // Try to find XR controllers
        var inputDevices = new List<InputDevice>();
        InputDevices.GetDevices(inputDevices);

        foreach (var device in inputDevices)
        {
            if (device.characteristics.HasFlag(InputDeviceCharacteristics.Left | InputDeviceCharacteristics.Controller))
            {
                Debug.Log($"Found left controller: {device.name}");
            }
            if (device.characteristics.HasFlag(InputDeviceCharacteristics.Right | InputDeviceCharacteristics.Controller))
            {
                Debug.Log($"Found right controller: {device.name}");
            }
        }
    }

    void Update()
    {
        if (!exerciseActive) return;

        // Check for grab inputs
        CheckGrabInput();

        // Check if exercise is complete
        if (Time.time - exerciseStartTime > exerciseDuration || successfulReaches >= targetsPerExercise)
        {
            EndExercise();
        }

        // Spawn new target if needed
        if (activeTargets.Count == 0 && successfulReaches < targetsPerExercise)
        {
            SpawnTarget();
        }
    }

    void StartExercise()
    {
        currentExercise++;
        totalReaches = 0;
        successfulReaches = 0;
        reachTimes.Clear();
        reachDistances.Clear();
        exerciseStartTime = Time.time;
        exerciseActive = true;

        SpawnTarget();

        if (instructionsText != null)
        {
            instructionsText.text = $"Exercise {currentExercise}\nReach for the targets!";
        }

        Debug.Log($"[VRRehabGame] Exercise {currentExercise} started (Difficulty: {rehabManager.CurrentDifficulty:F2})");
    }

    void SpawnTarget()
    {
        if (targetPrefab == null || playArea == null) return;

        // Calculate spawn parameters based on difficulty
        float difficulty = rehabManager.CurrentDifficulty;
        float spawnDistance = Mathf.Lerp(spawnDistanceRange.x, spawnDistanceRange.y, difficulty);
        float targetSize = Mathf.Lerp(targetSizeRange.x, targetSizeRange.y, difficulty);

        // Random position within reach
        Vector3 randomDir = Random.onUnitSphere;
        randomDir.y = Mathf.Abs(randomDir.y); // Keep above ground
        Vector3 spawnPos = playArea.position + randomDir * spawnDistance;

        // Create target
        GameObject targetObj = Instantiate(targetPrefab, spawnPos, Quaternion.identity, playArea);
        targetObj.transform.localScale = Vector3.one * targetSize;

        var target = targetObj.AddComponent<RehabTarget>();
        target.SpawnTime = Time.time;
        target.RequiresBothHands = requireBothHands;

        activeTargets.Add(target);

        Debug.Log($"[VRRehabGame] Target spawned at distance {spawnDistance:F2}m, size {targetSize:F2}");
    }

    void CheckGrabInput()
    {
        foreach (var target in activeTargets.ToArray())
        {
            if (target == null) continue;

            bool leftNear = IsNearController(target.transform.position, leftHandController);
            bool rightNear = IsNearController(target.transform.position, rightHandController);

            bool grabbed = false;
            if (target.RequiresBothHands)
            {
                grabbed = leftNear && rightNear;
            }
            else
            {
                grabbed = leftNear || rightNear;
            }

            if (grabbed)
            {
                OnTargetGrabbed(target);
            }
        }
    }

    bool IsNearController(Vector3 targetPos, Transform controller)
    {
        if (controller == null) return false;
        return Vector3.Distance(targetPos, controller.position) < grabDistance;
    }

    void OnTargetGrabbed(RehabTarget target)
    {
        successfulReaches++;
        totalReaches++;

        // Record metrics
        float reachTime = Time.time - target.SpawnTime;
        float reachDistance = Vector3.Distance(playArea.position, target.transform.position);
        
        reachTimes.Add(reachTime);
        reachDistances.Add(reachDistance);

        activeTargets.Remove(target);
        Destroy(target.gameObject);

        // Visual/audio feedback
        PlaySuccessFeedback();

        if (scoreText != null)
        {
            scoreText.text = $"Targets: {successfulReaches}/{targetsPerExercise}";
        }

        Debug.Log($"[VRRehabGame] Target reached in {reachTime:F2}s at distance {reachDistance:F2}m");
    }

    async void EndExercise()
    {
        exerciseActive = false;

        // Calculate performance metrics
        float accuracy = totalReaches > 0 ? (float)successfulReaches / targetsPerExercise : 0f;
        float avgReachTime = reachTimes.Count > 0 ? Average(reachTimes) : 0f;
        float avgReachDistance = reachDistances.Count > 0 ? Average(reachDistances) : 0f;

        // Normalize speed (faster = better, 0-1 range)
        float speedScore = avgReachTime > 0 ? Mathf.Clamp01(3f / avgReachTime) : 0f;

        Debug.Log($"[VRRehabGame] Exercise complete. Accuracy: {accuracy:P0}, " +
                 $"Avg Time: {avgReachTime:F2}s, Avg Distance: {avgReachDistance:F2}m");

        // Clear remaining targets
        foreach (var target in activeTargets)
        {
            if (target != null) Destroy(target.gameObject);
        }
        activeTargets.Clear();

        // Request adaptation with detailed metrics
        if (rehabManager != null && rehabManager.IsInitialized)
        {
            var additionalMetrics = new Dictionary<string, float>
            {
                ["reach_time"] = avgReachTime,
                ["reach_distance"] = avgReachDistance,
                ["speed_score"] = speedScore
            };

            await rehabManager.RequestAdaptationAsync(accuracy, speedScore, additionalMetrics);
        }

        // Show results
        if (instructionsText != null)
        {
            instructionsText.text = $"Exercise Complete!\n" +
                                   $"Accuracy: {accuracy:P0}\n" +
                                   $"Next exercise in 5 seconds...";
        }

        Invoke(nameof(StartExercise), 5f);
    }

    void OnAdaptationReceived(AdaptationDecision decision)
    {
        Debug.Log($"[VRRehabGame] AI Adaptation: {decision.Action} " +
                 $"(New Difficulty: {rehabManager.CurrentDifficulty:F2}, " +
                 $"Confidence: {decision.Confidence:F2})\n" +
                 $"Explanation: {decision.Explanation}");
    }

    void PlaySuccessFeedback()
    {
        // Add visual/audio feedback here
        // e.g., particle effects, sound, haptic feedback
    }

    float Average(List<float> values)
    {
        if (values.Count == 0) return 0f;
        float sum = 0f;
        foreach (float v in values) sum += v;
        return sum / values.Count;
    }

    void OnDestroy()
    {
        if (rehabManager != null)
        {
            rehabManager.OnSessionInitialized -= StartExercise;
            rehabManager.OnAdaptationReceived -= OnAdaptationReceived;
        }
    }
}

/// <summary>
/// Rehabilitation target component
/// </summary>
public class RehabTarget : MonoBehaviour
{
    public float SpawnTime { get; set; }
    public bool RequiresBothHands { get; set; }
}
