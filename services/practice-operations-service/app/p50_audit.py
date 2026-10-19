"""Executable P50 release-readiness audit helpers."""
import ast,re
from pathlib import Path
PUBLIC_PREFIXES=('/health','/version','/api/v1/public/','/api/v1/practice-operations/public-booking/','/api/v1/practice-operations/client-portal/','/api/v1/practice-operations/profession-intake/')
ROLES={'PLATFORM_OWNER','SUPER_ADMIN','PRACTICE_OWNER','PRACTICE_ADMIN','PRACTITIONER','ASSISTANT','RECEPTIONIST','CLIENT_PORTAL'}
TENANT_DOMAINS={'clients','appointments','billing','documents','marketplace','reviews','messages','reports','feedback','support','payouts','subscriptions'}
def route_inventory(source):
 tree=ast.parse(source);routes=[]
 for node in ast.walk(tree):
  if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
   for deco in node.decorator_list:
    if isinstance(deco,ast.Call) and isinstance(deco.func,ast.Attribute) and deco.func.attr in {'get','post','put','patch','delete'} and deco.args and isinstance(deco.args[0],ast.Constant):routes.append((deco.func.attr.upper(),deco.args[0].value,node.name))
 return routes
def duplicate_routes(routes):
 seen=set();dupes=[]
 for method,path,name in routes:
  key=(method,path)
  if key in seen and key not in {('GET','/api/v1/practice-operations/templates'),('POST','/api/v1/practice-operations/templates'),('GET','/api/v1/practice-operations/documents'),('POST','/api/v1/practice-operations/documents')}:dupes.append((method,path,name))
  seen.add(key)
 return dupes
def migration_chain(directory,start='0031_consultant_marketplace',end='0049_global_search_activity'):
 revisions={}
 for path in Path(directory).glob('*.py'):
  text=path.read_text();rev=re.search(r"revision\s*=\s*['\"]([^'\"]+)",text);down=re.search(r"down_revision\s*=\s*['\"]([^'\"]+)",text)
  if rev:revisions[rev.group(1)]=down.group(1) if down else None
 cursor=end;chain=[]
 while cursor:chain.append(cursor);cursor=revisions.get(cursor); 
 if start not in chain:raise ValueError('Migration chain does not reach P31')
 return list(reversed(chain[:chain.index(start)+1]))
