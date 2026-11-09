-- I want the rate to use only eligible vehicles in the selected group.
WITH filtered AS (
    SELECT makename, modelname, eligible_90d, sold_within_90d
    FROM vehicles
    WHERE (:makename IS NULL OR makename = :makename)
      AND (:modelname IS NULL OR modelname = :modelname)
      AND (:fueltype IS NULL OR fueltype = :fueltype)
      AND (:transmissiontype IS NULL OR transmissiontype = :transmissiontype)
      AND (:min_mileage IS NULL OR odometerkm >= :min_mileage)
      AND (:max_mileage IS NULL OR odometerkm <= :max_mileage)
), totals AS (
    SELECT 'overall' AS scope, NULL AS makename, NULL AS modelname,
           COALESCE(SUM(eligible_90d), 0) AS eligible,
           COALESCE(SUM(sold_within_90d), 0) AS sold_within_90d
    FROM filtered
    UNION ALL
    SELECT 'brand', makename, NULL, SUM(eligible_90d), SUM(sold_within_90d)
    FROM filtered
    GROUP BY makename
    UNION ALL
    SELECT 'model', makename, modelname, SUM(eligible_90d), SUM(sold_within_90d)
    FROM filtered
    GROUP BY makename, modelname
)
SELECT *, 1.0 * sold_within_90d / NULLIF(eligible, 0) AS rate
FROM totals
ORDER BY scope, makename, modelname;
