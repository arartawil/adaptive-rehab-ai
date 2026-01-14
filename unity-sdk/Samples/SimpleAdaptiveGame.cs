using UnityEngine;
using UnityEngine.UI;
using System.Collections.Generic;
using AdaptRehab;

/// <summary>
/// Simple example: Target shooting game with adaptive difficulty
/// Click targets that appear - difficulty adjusts based on accuracy
/// </summary>
public class SimpleAdaptiveGame : MonoBehaviour
{
    [Header("Game Objects")]
    public GameObject targetPrefab;
    public Transform spawnArea;
    public Text scoreText;
    public Text difficultyText;
    public Text statsText;

    [Header("Game Settings")]
    public int targetsPerRound = 5;
    public float roundDuration = 10f;

    private AdaptiveRehabManager rehabManager;
    private int score;
    private int hits;
    private int misses;
    private float roundStartTime;
    private List<GameObject> activeTargets = new List<GameObject>();
    private int currentRound;
    private bool roundActive;

    void Start()
    {
        // Get or add AdaptiveRehabManager
        rehabManager = FindObjectOfType<AdaptiveRehabManager>();
        if (rehabManager == null)
        {
            GameObject managerObj = new GameObject("AdaptiveRehabManager");
            rehabManager = managerObj.AddComponent<AdaptiveRehabManager>();
            rehabManager.serverHost = "localhost";
            rehabManager.serverPort = 8000;
            rehabManager.aiModule = AdaptiveRehabManager.AIModule.FuzzyLogic;
        }

        // Subscribe to events
        rehabManager.OnAdaptationReceived += OnAdaptationReceived;
        rehabManager.OnSessionInitialized += OnSessionInitialized;

        UpdateUI();
    }

    void OnSessionInitialized()
    {
        Debug.Log("[SimpleAdaptiveGame] Session initialized, starting first round");
        StartNewRound();
    }

    void Update()
    {
        if (!roundActive) return;

        // Check if round is over
        if (Time.time - roundStartTime > roundDuration || activeTargets.Count == 0)
        {
            EndRound();
        }

        UpdateUI();
    }

    void StartNewRound()
    {
        currentRound++;
        hits = 0;
        misses = 0;
        roundStartTime = Time.time;
        roundActive = true;

        // Spawn targets based on difficulty
        int targetCount = Mathf.RoundToInt(targetsPerRound * (0.5f + rehabManager.CurrentDifficulty));
        for (int i = 0; i < targetCount; i++)
        {
            SpawnTarget();
        }

        Debug.Log($"[SimpleAdaptiveGame] Round {currentRound} started with {targetCount} targets");
    }

    void SpawnTarget()
    {
        if (targetPrefab == null || spawnArea == null) return;

        // Random position within spawn area
        Vector3 randomPos = new Vector3(
            Random.Range(-5f, 5f),
            Random.Range(0f, 3f),
            Random.Range(-2f, 2f)
        );

        GameObject target = Instantiate(targetPrefab, spawnArea.position + randomPos, Quaternion.identity, spawnArea);
        
        // Scale based on difficulty (harder = smaller)
        float scale = Mathf.Lerp(1.5f, 0.5f, rehabManager.CurrentDifficulty);
        target.transform.localScale = Vector3.one * scale;

        // Add click handler
        var button = target.GetComponent<Button>();
        if (button == null)
        {
            button = target.AddComponent<Button>();
        }
        button.onClick.AddListener(() => OnTargetClicked(target));

        activeTargets.Add(target);
    }

    void OnTargetClicked(GameObject target)
    {
        hits++;
        score += 10;
        activeTargets.Remove(target);
        Destroy(target);

        Debug.Log($"[SimpleAdaptiveGame] Target hit! Score: {score}");
    }

    async void EndRound()
    {
        roundActive = false;

        // Calculate accuracy
        int totalTargets = hits + activeTargets.Count;
        float accuracy = totalTargets > 0 ? (float)hits / totalTargets : 0f;

        // Count remaining targets as misses
        misses = activeTargets.Count;

        // Clear remaining targets
        foreach (var target in activeTargets)
        {
            if (target != null) Destroy(target);
        }
        activeTargets.Clear();

        Debug.Log($"[SimpleAdaptiveGame] Round {currentRound} ended. Accuracy: {accuracy:P0}");

        // Request adaptation
        if (rehabManager != null && rehabManager.IsInitialized)
        {
            await rehabManager.RequestAdaptationAsync(accuracy);
        }

        // Start next round after delay
        Invoke(nameof(StartNewRound), 2f);
    }

    void OnAdaptationReceived(AdaptationDecision decision)
    {
        Debug.Log($"[SimpleAdaptiveGame] AI Decision: {decision.Action} " +
                 $"(Difficulty: {rehabManager.CurrentDifficulty:F2}, " +
                 $"Confidence: {decision.Confidence:F2})");

        // You can add visual feedback here (e.g., show message, play sound)
    }

    void UpdateUI()
    {
        if (scoreText != null)
            scoreText.text = $"Score: {score}";

        if (difficultyText != null && rehabManager != null)
            difficultyText.text = $"Difficulty: {rehabManager.CurrentDifficulty:P0}";

        if (statsText != null)
        {
            statsText.text = $"Round: {currentRound}\n" +
                           $"Hits: {hits}\n" +
                           $"Active Targets: {activeTargets.Count}";
        }
    }

    void OnDestroy()
    {
        if (rehabManager != null)
        {
            rehabManager.OnAdaptationReceived -= OnAdaptationReceived;
            rehabManager.OnSessionInitialized -= OnSessionInitialized;
        }
    }
}
