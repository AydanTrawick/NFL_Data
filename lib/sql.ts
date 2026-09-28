import parserModule from 'node-sql-parser';
const {Parser}=parserModule;
const tables=new Set(['teams','players','games','situations']);
const functions=new Set(['COUNT','SUM','AVG','MIN','MAX','ROUND','COALESCE','NULLIF','UPPER','LOWER','ABS']);
export function validateSQL(sql:string){
 if(sql.length>4000||!/^\s*SELECT\b/i.test(sql)||/[;]|--|\/\*|\b(?:attach|copy|pragma|install|load|read_\w+|write_\w+|query|execute|system|setseed)\b/i.test(sql))throw Error('Only one read-only SELECT is allowed.');
 const ast=new Parser().astify(sql,{database:'Postgresql'}) as any;
 if(Array.isArray(ast)||ast.type!=='select'||ast.with||ast._next||ast.into?.position||ast.locking_read||ast.from?.length!==1||!tables.has(ast.from[0].table)||ast.from[0].db||ast.from[0].expr||ast.from[0].join)throw Error('Select from one approved aggregate table.');
 function walk(node:any,root=false){if(!node||typeof node!=='object')return;if(Array.isArray(node)){node.forEach(n=>walk(n));return}if(!root&&node.type==='select')throw Error('Nested queries are unavailable.');if(node.type==='function'||node.type==='aggr_func'){const name=typeof node.name==='string'?node.name:node.name?.name?.map((n:any)=>n.value).join('');if(!functions.has(String(name).toUpperCase()))throw Error('This function is not allowed.')}Object.values(node).forEach(x=>walk(x));}
 walk(ast,true);return sql.trim();
}
