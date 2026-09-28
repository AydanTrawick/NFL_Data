export const questions=[
 {question:'Which teams passed most often?',sql:'SELECT team, ROUND("passRate" * 100, 1) AS pass_percent FROM teams ORDER BY "passRate" DESC LIMIT 10'},
 {question:'Who had the most rushing and receiving yards?',sql:'SELECT name, team, yards FROM players ORDER BY yards DESC LIMIT 10'},
 {question:'Who had the most passing yards?',sql:'SELECT name, team, "passingYards" FROM players ORDER BY "passingYards" DESC LIMIT 10'},
 {question:'Who had the most receptions?',sql:'SELECT name, team, receptions FROM players ORDER BY receptions DESC LIMIT 10'},
 {question:'Who broke the most tackles?',sql:'SELECT name, team, "brokenTackles" FROM players ORDER BY "brokenTackles" DESC LIMIT 10'},
 {question:'Who had the most yards after catch?',sql:'SELECT name, team, yac FROM players ORDER BY yac DESC LIMIT 10'},
 {question:'Which teams used motion most often?',sql:'SELECT team, ROUND("motionRate" * 100, 1) AS motion_percent FROM teams ORDER BY "motionRate" DESC LIMIT 10'},
 {question:'Which teams sent blitzes most often?',sql:'SELECT team, ROUND("blitzSentRate" * 100, 1) AS blitz_percent FROM teams ORDER BY "blitzSentRate" DESC LIMIT 10'},
 {question:'How often did teams run on third down?',sql:'SELECT SUM(run) AS runs, SUM("pass") AS passes, ROUND(100.0 * SUM(run) / NULLIF(SUM(total), 0), 1) AS run_percent FROM situations WHERE down = 3'},
 {question:'Who had the most charted QB hits?',sql:'SELECT name, team, "qbHits" FROM players ORDER BY "qbHits" DESC LIMIT 10'},
];
