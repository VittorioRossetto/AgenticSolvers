-- Step 1: best objectives per instance
CREATE TEMP VIEW best_objectives AS
SELECT
    problem,
    instance,
    MIN(quality) AS best_min,
    MAX(quality) AS best_max
FROM result
WHERE challenge = 2025
  AND quality IS NOT NULL
GROUP BY problem, instance;

-- Step 2 + 3: compute per-solver problem score and rank
WITH scored AS (
    SELECT
      r.problem,
      r.solver,
      r.instance,
      CASE
        WHEN p.kind = 'SAT' THEN
          CASE WHEN r.solved = 1 THEN 1.0 ELSE 0.0 END
        WHEN r.complete = 1 THEN
          1.0
        WHEN r.quality IS NULL THEN
          0.0
        WHEN p.kind = 'MIN' THEN
          POWER(CAST(b.best_min AS REAL) / r.quality, 0.25)
        WHEN p.kind = 'MAX' THEN
          POWER(r.quality / CAST(b.best_max AS REAL), 0.25)
      END AS score
    FROM result r
    JOIN problem p ON r.problem = p.name
    JOIN best_objectives b ON r.problem = b.problem AND r.instance = b.instance
    WHERE r.challenge = 2025
),
totals AS (
    SELECT
      problem,
      solver,
      SUM(score) AS total_score,
      RANK() OVER (PARTITION BY problem ORDER BY SUM(score) DESC) AS rnk
    FROM scored
    GROUP BY problem, solver
)
-- Step 4: build JSON per problem
SELECT json_group_object(
    problem,
    (
      SELECT json_group_array(
               json_object(
                 'solver', solver,
                 'score', ROUND(total_score, 3)
               )
             )
      FROM totals t2
      WHERE t2.problem = t1.problem AND t2.rnk <= 3
      ORDER BY total_score DESC
    )
)
FROM totals t1;
