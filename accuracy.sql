WITH merged AS (
	SELECT 
		c.article_a, c.article_b, 
		a1.subject s1, a2.subject s2
		from cache_d2v as c 
		LEFT JOIN articles a1 
		ON c.article_a = a1.index 
		LEFT JOIN articles a2 
		ON c.article_b = a2.index 
	)
SELECT count(*)
FROM merged 
WHERE s1 = s2
