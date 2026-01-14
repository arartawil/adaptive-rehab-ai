# Adaptive Rehab AI - Unity SDK

**Real-time AI-powered difficulty adaptation for Unity VR rehabilitation games**

## 📦 Installation

### Option 1: Unity Package Manager (Recommended)

1. Open Unity Package Manager (`Window > Package Manager`)
2. Click `+` → `Add package from git URL`
3. Enter: `https://github.com/arartawil/adaptive-rehab-ai.git?path=/unity-sdk`

### Option 2: Manual Installation

1. Download/clone this repository
2. Copy the `unity-sdk` folder to your Unity project's `Packages` folder
3. Unity will automatically detect and import the package

## ⚙️ Setup

### 1. Start the Python Server

```bash
cd adaptive-rehab-ai/service
python run_rest_server.py
```

Server will start at `http://localhost:8000`

### 2. Add Manager to Scene

**Option A: Automatic (Recommended)**
```csharp
// Manager will be created automatically when you use the API
// Just make sure the server is running
```

**Option B: Manual Setup**
1. Create empty GameObject in your scene
2. Add `AdaptiveRehabManager` component
3. Configure settings in Inspector:
   - Server Host: `localhost`
   - Server Port: `8000`
   - AI Module: Choose from Rule-based, Fuzzy Logic, or RL
   - Patient ID: Unique identifier
   - Initial Difficulty: 0.5 (0-1 range)

## 🚀 Quick Start

### Basic Example

```csharp
using UnityEngine;
using AdaptRehab;

public class MyGame : MonoBehaviour
{
    private AdaptiveRehabManager rehabManager;
    private float currentDifficulty = 0.5f;

    async void Start()
    {
        // Get or create manager
        rehabManager = FindObjectOfType<AdaptiveRehabManager>();
        if (rehabManager == null)
        {
            var managerObj = new GameObject("AdaptiveRehabManager");
            rehabManager = managerObj.AddComponent<AdaptiveRehabManager>();
        }

        // Subscribe to events
        rehabManager.OnAdaptationReceived += OnAdaptation;
        
        // Wait for initialization
        await rehabManager.InitializeAsync();
    }

    async void OnRoundComplete(float accuracy)
    {
        // Request adaptation
        var decision = await rehabManager.RequestAdaptationAsync(accuracy);
        
        if (decision != null)
        {
            // Update game difficulty
            currentDifficulty = rehabManager.CurrentDifficulty;
            UpdateGameDifficulty(currentDifficulty);
        }
    }

    void OnAdaptation(AdaptationDecision decision)
    {
        Debug.Log($"AI says: {decision.Action} difficulty!");
    }
}
```

## 🎮 Complete Examples

### 1. Simple Target Game

See [SimpleAdaptiveGame.cs](Samples/SimpleAdaptiveGame.cs)

**Features:**
- Click targets that appear on screen
- Difficulty adjusts target count and size
- Real-time adaptation based on accuracy

**Setup:**
1. Create empty scene
2. Add `SimpleAdaptiveGame` script
3. Assign target prefab (any clickable GameObject)
4. Run!

### 2. VR Rehabilitation Game

See [VRRehabilitationGame.cs](Samples/VRRehabilitationGame.cs)

**Features:**
- Reach and grab targets with VR controllers
- Difficulty adjusts distance and size
- Tracks accuracy, speed, and reach distance
- Uses Reinforcement Learning for personalization

**Setup:**
1. Use VR template project
2. Add `VRRehabilitationGame` script
3. Assign VR controllers
4. Assign target prefab
5. Run in VR

## 📚 API Reference

### AdaptiveRehabManager

Main component for managing adaptation sessions.

#### Properties

```csharp
// Configuration
string serverHost;              // Server address (default: localhost)
int serverPort;                 // Server port (default: 8000)
string sessionId;               // Unique session ID
AIModule aiModule;              // Rule-based, Fuzzy Logic, or RL
string patientId;               // Patient/user identifier
float initialDifficulty;        // Starting difficulty (0-1)

// Status (Read-only)
bool IsConnected;               // Server connection status
bool IsInitialized;             // Session initialization status
float CurrentDifficulty;        // Current difficulty level
AdaptationDecision LastDecision; // Last received decision
```

#### Methods

```csharp
// Initialize connection and session
Task<bool> InitializeAsync()

// Request adaptation decision
Task<AdaptationDecision> RequestAdaptationAsync(
    float accuracy,                                    // Required: 0-1
    float speed = 1.0f,                               // Optional: performance speed
    Dictionary<string, float> additionalMetrics = null // Optional: custom metrics
)

// Manually set difficulty (for testing)
void SetDifficulty(float difficulty)
```

#### Events

```csharp
// Fired when adaptation received from server
event Action<AdaptationDecision> OnAdaptationReceived;

// Fired when session initialized successfully
event Action OnSessionInitialized;

// Fired when session ended
event Action OnSessionEnded;
```

### AdaptationDecision

AI decision output.

```csharp
public class AdaptationDecision
{
    AdaptationAction Action;      // Increase, Decrease, or Maintain
    float Magnitude;              // How much to change (0-1)
    Dictionary Parameters;        // Additional parameters
    float Confidence;             // AI confidence (0-1)
    string Explanation;           // Human-readable reasoning
    
    // Helper method
    float GetDifficultyChange();  // Get difficulty change amount
}
```

### AdaptationAction

```csharp
public enum AdaptationAction
{
    Increase,   // Make it harder
    Decrease,   // Make it easier
    Maintain    // Keep current difficulty
}
```

### StateVector

Performance data sent to AI.

```csharp
public class StateVector
{
    Dictionary<string, float> PerformanceMetrics;  // accuracy, speed, etc.
    Dictionary<string, float> SensorData;          // hand position, velocity, etc.
    Dictionary<string, object> TaskState;          // difficulty, round, etc.
    float Timestamp;
    string SessionId;
}
```

## 🤖 AI Modules

### Rule-Based (Threshold)
- **Best for**: Quick setup, predictable behavior
- **How it works**: IF accuracy > 70% THEN increase
- **Speed**: <0.5ms
- **Training**: None required

### Fuzzy Logic (Linguistic Rules)
- **Best for**: Smooth adaptations, medical apps
- **How it works**: Uses LOW/MEDIUM/HIGH linguistic variables
- **Speed**: ~1ms
- **Training**: None required

### Reinforcement Learning (Q-Learning)
- **Best for**: Personalization, long-term optimization
- **How it works**: Learns optimal policy through experience
- **Speed**: ~1ms
- **Training**: Improves over 30-50 episodes

**Choose based on your needs:**
- Start with **Rule-based** for quick testing
- Use **Fuzzy Logic** for smooth, human-like adaptation
- Use **RL** for personalized, long-term optimization

## 🔧 Advanced Usage

### Custom Metrics

```csharp
// Include additional performance data
var customMetrics = new Dictionary<string, float>
{
    ["reaction_time"] = 0.5f,
    ["error_rate"] = 0.1f,
    ["engagement_score"] = 0.8f
};

await rehabManager.RequestAdaptationAsync(
    accuracy: 0.75f,
    speed: 1.2f,
    additionalMetrics: customMetrics
);
```

### VR Sensor Data

```csharp
// Send VR tracking data (for advanced adaptation)
var state = new StateVector
{
    PerformanceMetrics = new Dictionary<string, float>
    {
        ["accuracy"] = CalculateAccuracy(),
        ["completion_time"] = GetCompletionTime()
    },
    SensorData = new Dictionary<string, float>
    {
        ["hand_velocity"] = GetHandVelocity(),
        ["reach_distance"] = GetReachDistance(),
        ["head_rotation"] = GetHeadRotation()
    }
};

var decision = await client.GetAdaptationAsync(state);
```

### Error Handling

```csharp
async void RequestAdaptation()
{
    try
    {
        var decision = await rehabManager.RequestAdaptationAsync(accuracy);
        
        if (decision == null)
        {
            Debug.LogWarning("Failed to get adaptation, using fallback");
            UseFallbackDifficulty();
            return;
        }
        
        ApplyAdaptation(decision);
    }
    catch (Exception ex)
    {
        Debug.LogError($"Adaptation error: {ex.Message}");
        UseFallbackDifficulty();
    }
}
```

### Session Management

```csharp
// End session manually
await rehabManager.EndSessionAsync();

// Re-initialize with different module
rehabManager.aiModule = AdaptiveRehabManager.AIModule.ReinforcementLearning;
await rehabManager.InitializeAsync();
```

## 🐛 Troubleshooting

### "Cannot connect to server"

**Solution:**
1. Make sure Python server is running:
   ```bash
   python service/run_rest_server.py
   ```
2. Check server logs for errors
3. Verify firewall isn't blocking port 8000
4. Try `curl http://localhost:8000/health`

### "Session not initialized"

**Solution:**
- Wait for `OnSessionInitialized` event before requesting adaptations
- Check Unity console for initialization errors
- Verify server is responding

### Slow/No Response

**Solution:**
- Check network latency
- Verify server isn't overloaded
- Use `await` properly with async methods
- Check for exceptions in Unity console

### JSON Parsing Errors

**Solution:**
- Ensure Newtonsoft.Json is installed
- Unity 2020.3+ includes it by default
- For older versions: Install via Package Manager

## 📊 Performance

- **Latency**: ~5-10ms per adaptation request (REST API)
- **Throughput**: 500+ requests/sec
- **Memory**: <5MB overhead
- **Battery Impact**: Minimal (async operations)

## 🔒 Dependencies

- **Unity**: 2020.3 or higher
- **Newtonsoft.Json**: Included in Unity 2020.3+
- **Server**: Python 3.8+ with Adaptive Rehab AI

## 📖 Additional Resources

- [Main Documentation](https://github.com/arartawil/adaptive-rehab-ai/blob/main/README.md)
- [Python API Reference](https://github.com/arartawil/adaptive-rehab-ai/blob/main/RL_IMPLEMENTATION.md)
- [Web Demo](https://github.com/arartawil/adaptive-rehab-ai/tree/main/web-demo)

## 💬 Support

- **Issues**: [GitHub Issues](https://github.com/arartawil/adaptive-rehab-ai/issues)
- **Discussions**: [GitHub Discussions](https://github.com/arartawil/adaptive-rehab-ai/discussions)

## 📄 License

MIT License - Same as main package

---

**Made with ❤️ for VR rehabilitation and adaptive gaming**
