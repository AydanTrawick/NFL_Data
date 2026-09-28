import {DuckDBInstance} from '@duckdb/node-api';
import path from 'node:path';
import {validateSQL} from './sql';
let database:Promise<DuckDBInstance>|undefined;
async function initialize(){const db=await DuckDBInstance.create(':memory:',{threads:'1',memory_limit:'128MB',max_temp_directory_size:'0B',autoload_known_extensions:'false',autoinstall_known_extensions:'false'});const c=await db.connect();try{for(const name of ['teams','players','games','situations']){const file=path.join(process.cwd(),'data','analytics',name+'.parquet').replace(/'/g,"''");await c.run(`CREATE TABLE ${name} AS SELECT * FROM read_parquet('${file}')`)}await c.run('SET enable_external_access = false');await c.run('SET lock_configuration = true');}finally{c.closeSync()}return db;}
export async function querySQL(sql:string){validateSQL(sql);database??=initialize().catch(e=>{database=undefined;throw e});const db=await database,c=await db.connect();const timer=setTimeout(()=>c.interrupt(),2500);try{const result=await c.runAndReadAll(`SELECT * FROM (${sql}) AS safe_result LIMIT 500`);return result.getRowObjectsJson()}finally{clearTimeout(timer);c.closeSync()}}
