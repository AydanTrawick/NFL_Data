import {describe,it,expect} from 'vitest';
import {questions} from '../lib/questions';
import {validateSQL} from '../lib/sql';
import {querySQL} from '../lib/duckdb';
describe('Film Room read-only query boundary',()=>{
 for(const q of questions)it(q.question,async()=>{expect(validateSQL(q.sql)).toBe(q.sql);const rows=await querySQL(q.sql);expect(rows.length).toBeGreaterThan(0);expect(rows.length).toBeLessThanOrEqual(500)});
 for(const sql of ["SELECT * FROM read_csv('/etc/passwd')","SELECT * FROM teams; DROP TABLE teams","SELECT * FROM duckdb_settings()","SELECT * FROM teams JOIN players ON true","SELECT * FROM (SELECT * FROM teams) x","SELECT query('delete from teams') FROM teams","COPY teams TO '/tmp/x'","SELECT * FROM information_schema.tables","SELECT * FROM teams UNION SELECT * FROM players"]){it('rejects '+sql,()=>expect(()=>validateSQL(sql)).toThrow())}
 it('matches a known aggregate',async()=>{const rows=await querySQL('SELECT COUNT(*) AS teams FROM teams');expect(Number(rows[0].teams)).toBe(32)})
});
