import type {NextConfig} from 'next';
const config:NextConfig={serverExternalPackages:['@duckdb/node-api','@duckdb/node-bindings','node-sql-parser'],outputFileTracingIncludes:{'/api/ask':['./data/analytics/*.parquet']}};
export default config;
