# 7. Thiết Kế Sequence Diagram

## 7.1 Main Processing Sequence

```
┌─────────┐  ┌──────────┐  ┌────────────┐  ┌──────┐  ┌────────┐  ┌─────────┐  ┌──────────┐  ┌────────┐  ┌──────┐  ┌────┐
│SQS Queue│  │WorkerMgr │  │JobProcessor│  │S3    │  │Parser  │  │Extractor│  │Matcher   │  │Scorer  │  │AI    │  │ DB │
└────┬────┘  └────┬─────┘  └─────┬──────┘  └──┬───┘  └───┬────┘  └────┬────┘  └────┬─────┘  └───┬────┘  └──┬───┘  └─┬──┘
     │            │               │             │          │            │            │            │          │        │
     │◀──poll()───│               │             │          │            │            │            │          │        │
     │───message──▶               │             │          │            │            │            │          │        │
     │            │──process(msg)─▶             │          │            │            │            │          │        │
     │            │               │             │          │            │            │            │          │        │
     │            │               │──update_status('processing')────────────────────────────────────────────────────▶│
     │            │               │             │          │            │            │            │          │        │
     │            │               │──download───▶          │            │            │            │          │        │
     │            │               │◀──bytes──────          │            │            │            │          │        │
     │            │               │             │          │            │            │            │          │        │
     │            │               │──parse(bytes)─────────▶│            │            │            │          │        │
     │            │               │◀──DocumentContent──────│            │            │            │          │        │
     │            │               │             │          │            │            │            │          │        │
     │            │               │──extract(resume_text)──────────────▶│            │            │          │        │
     │            │               │◀──resume_skills─────────────────────│            │            │          │        │
     │            │               │             │          │            │            │            │          │        │
     │            │               │──extract(jd_text)──────────────────▶│            │            │          │        │
     │            │               │◀──jd_skills────────────────────────│            │            │          │        │
     │            │               │             │          │            │            │            │          │        │
     │            │               │──match(resume_skills, jd_skills)────────────────▶│            │          │        │
     │            │               │◀──MatchResult───────────────────────────────────│            │          │        │
     │            │               │             │          │            │            │            │          │        │
     │            │               │──calculate(match_result)────────────────────────────────────▶│          │        │
     │            │               │◀──ScoreResult───────────────────────────────────────────────│          │        │
     │            │               │             │          │            │            │            │          │        │
     │            │               │──analyze(texts, match, score)─────────────────────────────────────────▶│        │
     │            │               │◀──AIAnalysis──────────────────────────────────────────────────────────│        │
     │            │               │             │          │            │            │            │          │        │
     │            │               │──save_result(report)─────────────────────────────────────────────────────────────▶
     │            │               │──update_status('completed')──────────────────────────────────────────────────────▶
     │            │               │◀──success─────────────────────────────────────────────────────────────────────────│
     │            │               │             │          │            │            │            │          │        │
     │            │◀──done─────────             │          │            │            │            │          │        │
     │◀─delete────│               │             │          │            │            │            │          │        │
     │            │               │             │          │            │            │            │          │        │
```

## 7.2 Error & Retry Sequence

```
┌─────────┐  ┌──────────┐  ┌────────────┐  ┌──────────┐  ┌─────┐
│SQS Queue│  │WorkerMgr │  │JobProcessor│  │RetryHandler│  │ DB  │
└────┬────┘  └────┬─────┘  └─────┬──────┘  └─────┬─────┘  └──┬──┘
     │            │               │                │           │
     │◀──poll()───│               │                │           │
     │───message──▶               │                │           │
     │            │──process(msg)─▶                │           │
     │            │               │                │           │
     │            │               │──── ERROR ─────┤           │
     │            │               │                │           │
     │            │               │──can_retry()?──▶           │
     │            │               │◀──yes───────────           │
     │            │               │                │           │
     │            │               │──increment_retry()────────────────▶│
     │            │               │                │           │◀──ok──│
     │            │               │                │           │
     │            │               │──wait(backoff)─▶           │
     │            │               │◀───────────────            │
     │            │               │                │           │
     │            │               │── RETRY PROCESS ───────────│
     │            │               │                │           │
     │            │               │──── ERROR (again) ─────────│
     │            │               │                │           │
     │            │               │──can_retry()?──▶           │
     │            │               │◀──no (max reached)─────────│
     │            │               │                │           │
     │            │               │──mark_failed(error_msg)────────────▶│
     │            │◀──failed───────                │           │
     │            │               │                │           │
     │◀─send_dlq─│               │                │           │
     │◀─delete───│               │                │           │
     │            │               │                │           │
```

## 7.3 Skill Matching Detail Sequence

```
┌────────────┐  ┌────────────┐  ┌────────────┐  ┌───────────────┐
│HybridMatch │  │ExactMatcher│  │FuzzyMatcher│  │SemanticMatcher│
└─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └──────┬────────┘
      │                │               │                 │
      │──exact_match───▶               │                 │
      │◀──exact_results─               │                 │
      │                │               │                 │
      │  (remove already matched from candidate pool)    │
      │                │               │                 │
      │──fuzzy_match(remaining)────────▶                 │
      │◀──fuzzy_results────────────────│                 │
      │                │               │                 │
      │  (filter by threshold >= 0.80)                   │
      │  (remove fuzzy matched from candidate pool)      │
      │                │               │                 │
      │──semantic_match(remaining)─────────────────────▶│
      │◀──semantic_results─────────────────────────────│
      │                │               │                 │
      │  (filter by threshold >= 0.75)                   │
      │                │               │                 │
      │──merge_results()               │                 │
      │  (deduplicate, rank by confidence)               │
      │                │               │                 │
      │──return MatchResult            │                 │
      │                │               │                 │
```

## 7.4 AI Analysis Sequence

```
┌───────────────┐  ┌─────────────┐  ┌──────────────┐  ┌──────────┐
│AnalysisService│  │PromptBuilder│  │OpenAIClient  │  │RespParser│
└──────┬────────┘  └──────┬──────┘  └──────┬───────┘  └────┬─────┘
       │                   │                │                │
       │──build_prompt()──▶│                │                │
       │  (resume_text,    │                │                │
       │   jd_text,        │                │                │
       │   match_result,   │                │                │
       │   score)          │                │                │
       │◀──prompt_str──────│                │                │
       │                   │                │                │
       │──analyze(prompt)──────────────────▶│                │
       │                   │                │──API call──▶   │
       │                   │                │  (GPT-4o)      │
       │                   │                │◀──response──   │
       │◀──raw_response────────────────────│                │
       │                   │                │                │
       │──parse(raw_response)──────────────────────────────▶│
       │                   │                │                │◀──validate JSON
       │◀──AIAnalysis──────────────────────────────────────│
       │                   │                │                │
       │  (if parse fails, retry with simpler prompt)       │
       │                   │                │                │
```

## 7.5 Worker Startup Sequence

```
┌──────┐  ┌──────────┐  ┌──────────┐  ┌────────┐  ┌─────────────┐  ┌──────────────┐
│main()│  │Settings  │  │DBPool    │  │AWSClients│ │ModelLoader  │  │WorkerManager │
└──┬───┘  └────┬─────┘  └────┬─────┘  └────┬────┘  └──────┬──────┘  └──────┬───────┘
   │           │              │              │              │                │
   │──load()──▶│              │              │              │                │
   │◀──config──│              │              │              │                │
   │           │              │              │              │                │
   │──init_pool(config)──────▶│              │              │                │
   │◀──pool────────────────── │              │              │                │
   │           │              │              │              │                │
   │──init_clients(config)───────────────────▶              │                │
   │◀──sqs, s3─────────────────────────────── │              │                │
   │           │              │              │              │                │
   │──load_model()──────────────────────────────────────────▶                │
   │◀──sentence_transformer──────────────────────────────────│                │
   │           │              │              │              │                │
   │──create(workers=3)──────────────────────────────────────────────────────▶│
   │           │              │              │              │                │
   │──start()──────────────────────────────────────────────────────────────▶│
   │           │              │              │              │                │──spawn threads
   │           │              │              │              │                │──register signals
   │◀──running──────────────────────────────────────────────────────────────│
   │           │              │              │              │                │
```

## 7.6 Graceful Shutdown Sequence

```
┌────────┐  ┌──────────────┐  ┌─────────────┐  ┌─────────┐  ┌────┐
│OS/Docker│  │WorkerManager │  │WorkerThreads│  │SQS      │  │ DB │
└───┬────┘  └──────┬───────┘  └──────┬──────┘  └────┬────┘  └─┬──┘
    │              │                  │               │         │
    │──SIGTERM────▶│                  │               │         │
    │              │                  │               │         │
    │              │──set_shutdown()──▶               │         │
    │              │  (stop polling)  │               │         │
    │              │                  │               │         │
    │              │──wait(timeout=60s)               │         │
    │              │                  │               │         │
    │              │  [in-flight jobs finish]         │         │
    │              │◀──all_done────────               │         │
    │              │                  │               │         │
    │              │                  │  [OR timeout] │         │
    │              │──release_msgs()──────────────────▶         │
    │              │  (change visibility to 0)        │         │
    │              │                  │               │         │
    │              │──close()─────────────────────────────────▶│
    │              │◀──closed─────────────────────────────────│
    │              │                  │               │         │
    │◀──exit(0)────│                  │               │         │
    │              │                  │               │         │
```
