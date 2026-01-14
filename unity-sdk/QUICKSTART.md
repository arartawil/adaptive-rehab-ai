# Unity SDK Quick Setup Guide

## 🎮 Get Started in 5 Minutes

### Prerequisites
- Unity 2020.3 or higher
- Python 3.8+ (for server)

### Step 1: Install Unity Package

**Option A: Package Manager (Recommended)**
1. Open Unity Package Manager (`Window > Package Manager`)
2. Click `+` → `Add package from git URL`
3. Paste: `https://github.com/arartawil/adaptive-rehab-ai.git?path=/unity-sdk`
4. Click `Add`

**Option B: Manual**
1. Clone/download this repository
2. Copy `unity-sdk/` folder to your project's `Packages/` folder

### Step 2: Start Python Server

```bash
cd adaptive-rehab-ai/service
pip install -r requirements.txt
python run_rest_server.py
```

Server starts at `http://localhost:8000`

### Step 3: Add to Scene

Add this script to any GameObject:

```csharp
using UnityEngine;
using AdaptRehab;

public class MyAdaptiveGame : MonoBehaviour
{
    private AdaptiveRehabManager rehabManager;

    async void Start()
    {
        // Auto-create manager
        rehabManager = FindObjectOfType<AdaptiveRehabManager>();
        if (rehabManager == null)
        {
            var managerObj = new GameObject("AdaptiveRehabManager");
            rehabManager = managerObj.AddComponent<AdaptiveRehabManager>();
        }

        // Subscribe to events
        rehabManager.OnAdaptationReceived += OnAdaptation;
        
        // Initialize
        await rehabManager.InitializeAsync();
    }

    async void OnGameRoundComplete(float accuracy)
    {
        // Request AI adaptation
        var decision = await rehabManager.RequestAdaptationAsync(accuracy);
        
        // Update game difficulty
        float newDifficulty = rehabManager.CurrentDifficulty;
        Debug.Log($"New difficulty: {newDifficulty}");
    }

    void OnAdaptation(AdaptationDecision decision)
    {
        Debug.Log($"AI says: {decision.Action} difficulty!");
    }
}
```

### Step 4: Run & Test

1. Press Play in Unity
2. Check Console for "Session initialized"
3. Play your game - difficulty adapts automatically!

## 🎯 Examples Included

1. **SimpleAdaptiveGame.cs** - Click target game (basic example)
2. **VRRehabilitationGame.cs** - VR hand tracking game (advanced)

Import from Package Manager samples!

## 🤖 Choose AI Module

```csharp
// In Inspector or code:
rehabManager.aiModule = AdaptiveRehabManager.AIModule.RuleBased;        // Fast, predictable
rehabManager.aiModule = AdaptiveRehabManager.AIModule.FuzzyLogic;       // Smooth, linguistic
rehabManager.aiModule = AdaptiveRehabManager.AIModule.ReinforcementLearning; // Learns over time
```

## 🐛 Troubleshooting

**"Cannot connect to server"**
- Make sure Python server is running: `python run_rest_server.py`
- Check `http://localhost:8000/health` in browser

**"Session not initialized"**
- Wait for `OnSessionInitialized` event before requesting adaptations

**JSON errors**
- Unity 2020.3+ includes Newtonsoft.Json by default
- For older Unity: Install via Package Manager

## 📖 Full Documentation

See [unity-sdk/README.md](README.md) for complete API reference and advanced usage.

## 💬 Need Help?

- [GitHub Issues](https://github.com/arartawil/adaptive-rehab-ai/issues)
- [Discussions](https://github.com/arartawil/adaptive-rehab-ai/discussions)

---

**Happy adaptive gaming! 🎮🧠**
