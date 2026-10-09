import { build } from 'vite'
import { execFileSync } from 'node:child_process'
import { resolve } from 'node:path'
const integration=process.argv.includes('--integration')
const entries=integration?['api-integration']:['local-provider','api-provider','scenario','highlight','monitoring']
for(const name of entries){
 await build({configFile:false,build:{outDir:'.test-dist',emptyOutDir:false,lib:{entry:resolve('tests/'+name+'.test.ts'),formats:['es'],fileName:()=>name+'.test.mjs'},rollupOptions:{external:['node:test','node:assert/strict']}}})
 execFileSync(process.execPath,['--test',resolve('.test-dist/'+name+'.test.mjs')],{stdio:'inherit'})
}
