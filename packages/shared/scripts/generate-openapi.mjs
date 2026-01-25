import fs from 'node:fs/promises'
import path from 'node:path'
import openapiTS from 'openapi-typescript'

const apiUrl = process.env.API_OPENAPI_URL || 'http://localhost:8000/openapi.json'
const outFile = path.join(process.cwd(), 'src', 'openapi.ts')

const schema = await fetch(apiUrl).then((r) => {
  if (!r.ok) throw new Error(`Failed to fetch OpenAPI: ${r.status}`)
  return r.json()
})

const types = await openapiTS(schema, { exportType: true })
await fs.writeFile(outFile, types)
console.log(`Generated ${outFile} from ${apiUrl}`)

