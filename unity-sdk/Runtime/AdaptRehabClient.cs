using System;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using UnityEngine;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace AdaptRehab
{
    /// <summary>
    /// REST API client for Adaptive Rehab AI
    /// Uses HTTP REST API for communication (simpler than gRPC for Unity)
    /// </summary>
    public class AdaptRehabClient : IDisposable
    {
        private readonly HttpClient httpClient;
        private readonly string baseUrl;
        private string sessionId;
        private bool isInitialized;

        /// <summary>
        /// Create new client
        /// </summary>
        /// <param name="host">Server host (default: localhost)</param>
        /// <param name="port">Server port (default: 8000)</param>
        public AdaptRehabClient(string host = "localhost", int port = 8000)
        {
            baseUrl = $"http://{host}:{port}";
            httpClient = new HttpClient { Timeout = TimeSpan.FromSeconds(30) };
            
            Debug.Log($"[AdaptRehabClient] Created client for {baseUrl}");
        }

        /// <summary>
        /// Initialize session with AI module
        /// </summary>
        /// <param name="sessionId">Unique session identifier</param>
        /// <param name="moduleName">AI module: "rule_based", "fuzzy_logic", or "reinforcement_learning"</param>
        /// <param name="patientProfile">Patient profile data</param>
        /// <param name="taskConfig">Task configuration</param>
        public async Task<bool> InitSessionAsync(
            string sessionId,
            string moduleName = "rule_based",
            PatientProfile patientProfile = null,
            TaskConfig taskConfig = null)
        {
            try
            {
                this.sessionId = sessionId;

                // Build request payload
                var payload = new JObject
                {
                    ["session_id"] = sessionId,
                    ["module_name"] = moduleName,
                    ["patient_profile"] = JObject.FromObject(patientProfile ?? new PatientProfile(sessionId)),
                    ["task_config"] = JObject.FromObject(taskConfig ?? new TaskConfig("unity_game"))
                };

                var content = new StringContent(
                    payload.ToString(),
                    Encoding.UTF8,
                    "application/json"
                );

                Debug.Log($"[AdaptRehabClient] Initializing session {sessionId} with module {moduleName}");

                var response = await httpClient.PostAsync($"{baseUrl}/session/init", content);
                response.EnsureSuccessStatusCode();

                var responseContent = await response.Content.ReadAsStringAsync();
                var result = JObject.Parse(responseContent);

                isInitialized = result["status"]?.ToString() == "initialized";

                if (isInitialized)
                {
                    Debug.Log($"[AdaptRehabClient] Session initialized successfully");
                }
                else
                {
                    Debug.LogError($"[AdaptRehabClient] Session initialization failed: {responseContent}");
                }

                return isInitialized;
            }
            catch (Exception ex)
            {
                Debug.LogError($"[AdaptRehabClient] Error initializing session: {ex.Message}");
                return false;
            }
        }

        /// <summary>
        /// Get adaptation decision from AI
        /// </summary>
        /// <param name="state">Current state vector</param>
        /// <returns>Adaptation decision or null if error</returns>
        public async Task<AdaptationDecision> GetAdaptationAsync(StateVector state)
        {
            if (!isInitialized)
            {
                Debug.LogError("[AdaptRehabClient] Session not initialized. Call InitSessionAsync first.");
                return null;
            }

            try
            {
                state.SessionId = sessionId;
                state.Timestamp = Time.time;

                // Build request payload
                var payload = new JObject
                {
                    ["session_id"] = sessionId,
                    ["state"] = new JObject
                    {
                        ["performance_metrics"] = JObject.FromObject(state.PerformanceMetrics),
                        ["sensor_data"] = JObject.FromObject(state.SensorData),
                        ["task_state"] = JObject.FromObject(state.TaskState),
                        ["timestamp"] = state.Timestamp,
                        ["session_id"] = state.SessionId
                    }
                };

                var content = new StringContent(
                    payload.ToString(),
                    Encoding.UTF8,
                    "application/json"
                );

                var response = await httpClient.PostAsync($"{baseUrl}/adapt", content);
                response.EnsureSuccessStatusCode();

                var responseContent = await response.Content.ReadAsStringAsync();
                var result = JObject.Parse(responseContent);

                // Parse decision
                var decision = new AdaptationDecision
                {
                    Action = ParseAction(result["action"]?.ToString()),
                    Magnitude = result["magnitude"]?.Value<float>() ?? 0f,
                    Confidence = result["confidence"]?.Value<float>() ?? 0f,
                    Explanation = result["explanation"]?.ToString() ?? "",
                    Parameters = result["parameters"]?.ToObject<Dictionary<string, object>>() ?? new Dictionary<string, object>()
                };

                Debug.Log($"[AdaptRehabClient] Received decision: {decision.Action} (confidence: {decision.Confidence:F2})");

                return decision;
            }
            catch (Exception ex)
            {
                Debug.LogError($"[AdaptRehabClient] Error getting adaptation: {ex.Message}");
                return null;
            }
        }

        /// <summary>
        /// End session
        /// </summary>
        public async Task<bool> EndSessionAsync()
        {
            if (!isInitialized) return true;

            try
            {
                var payload = new JObject { ["session_id"] = sessionId };
                var content = new StringContent(
                    payload.ToString(),
                    Encoding.UTF8,
                    "application/json"
                );

                var response = await httpClient.PostAsync($"{baseUrl}/session/end", content);
                response.EnsureSuccessStatusCode();

                isInitialized = false;
                Debug.Log($"[AdaptRehabClient] Session ended successfully");

                return true;
            }
            catch (Exception ex)
            {
                Debug.LogError($"[AdaptRehabClient] Error ending session: {ex.Message}");
                return false;
            }
        }

        /// <summary>
        /// Check if server is reachable
        /// </summary>
        public async Task<bool> PingServerAsync()
        {
            try
            {
                var response = await httpClient.GetAsync($"{baseUrl}/health");
                return response.IsSuccessStatusCode;
            }
            catch
            {
                return false;
            }
        }

        private AdaptationAction ParseAction(string action)
        {
            return action?.ToLower() switch
            {
                "increase" => AdaptationAction.Increase,
                "decrease" => AdaptationAction.Decrease,
                "maintain" => AdaptationAction.Maintain,
                _ => AdaptationAction.Maintain
            };
        }

        public void Dispose()
        {
            httpClient?.Dispose();
        }
    }
}
