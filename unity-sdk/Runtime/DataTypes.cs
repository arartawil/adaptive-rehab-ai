using System;
using System.Collections.Generic;

namespace AdaptRehab
{
    /// <summary>
    /// Adaptation action types
    /// </summary>
    public enum AdaptationAction
    {
        Increase,
        Decrease,
        Maintain
    }

    /// <summary>
    /// State vector containing performance metrics and sensor data
    /// </summary>
    [Serializable]
    public class StateVector
    {
        public Dictionary<string, float> PerformanceMetrics { get; set; }
        public Dictionary<string, float> SensorData { get; set; }
        public Dictionary<string, object> TaskState { get; set; }
        public float Timestamp { get; set; }
        public string SessionId { get; set; }

        public StateVector()
        {
            PerformanceMetrics = new Dictionary<string, float>();
            SensorData = new Dictionary<string, float>();
            TaskState = new Dictionary<string, object>();
            Timestamp = Time.time;
        }
    }

    /// <summary>
    /// Adaptation decision from AI module
    /// </summary>
    [Serializable]
    public class AdaptationDecision
    {
        public AdaptationAction Action { get; set; }
        public float Magnitude { get; set; }
        public Dictionary<string, object> Parameters { get; set; }
        public float Confidence { get; set; }
        public string Explanation { get; set; }

        public AdaptationDecision()
        {
            Parameters = new Dictionary<string, object>();
        }

        /// <summary>
        /// Get difficulty change amount
        /// </summary>
        public float GetDifficultyChange()
        {
            if (Parameters.ContainsKey("difficulty_change"))
            {
                if (Parameters["difficulty_change"] is float change)
                    return change;
                if (Parameters["difficulty_change"] is double dChange)
                    return (float)dChange;
            }
            return 0f;
        }
    }

    /// <summary>
    /// Patient/user profile data
    /// </summary>
    [Serializable]
    public class PatientProfile
    {
        public string PatientId { get; set; }
        public float BaselinePerformance { get; set; }
        public Dictionary<string, object> AdditionalData { get; set; }

        public PatientProfile(string patientId)
        {
            PatientId = patientId;
            BaselinePerformance = 0.5f;
            AdditionalData = new Dictionary<string, object>();
        }
    }

    /// <summary>
    /// Task configuration
    /// </summary>
    [Serializable]
    public class TaskConfig
    {
        public string TaskType { get; set; }
        public float InitialDifficulty { get; set; }
        public Dictionary<string, object> AdditionalData { get; set; }

        public TaskConfig(string taskType)
        {
            TaskType = taskType;
            InitialDifficulty = 0.5f;
            AdditionalData = new Dictionary<string, object>();
        }
    }
}
