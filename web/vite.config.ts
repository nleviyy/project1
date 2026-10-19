import { randomUUID } from 'node:crypto'
import { spawn } from 'node:child_process'
import { existsSync, readFileSync, renameSync, writeFileSync } from 'node:fs'
import type { IncomingMessage, ServerResponse } from 'node:http'
import { resolve } from 'node:path'
import react from '@vitejs/plugin-react'
import { defineConfig, type Plugin } from 'vite'

type DataRecord = Record<string, unknown>
type Next = (error?: Error) => void

let dataDirectory = ''
let projectDirectory = ''

function readRecords(fileName: string): DataRecord[] {
  const contents = readFileSync(resolve(dataDirectory, fileName), 'utf-8')
  const records: unknown = JSON.parse(contents)
  if (!Array.isArray(records) || records.some((record) => typeof record !== 'object' || record === null)) {
    throw new Error(`${fileName} must contain a list of JSON objects.`)
  }
  return records
}

function writeRecordUpdates(updates: Record<string, DataRecord[]>): void {
  const staged = new Map<string, string>()
  const originals = new Map<string, Buffer | null>()
  const replaced: string[] = []
  try {
    for (const [fileName, records] of Object.entries(updates)) {
      const targetPath = resolve(dataDirectory, fileName)
      originals.set(fileName, readFileSync(targetPath))
      const temporaryPath = `${targetPath}.${randomUUID()}.tmp`
      writeFileSync(temporaryPath, `${JSON.stringify(records, null, 4)}\n`, 'utf-8')
      staged.set(fileName, temporaryPath)
    }
    for (const [fileName, temporaryPath] of staged) {
      renameSync(temporaryPath, resolve(dataDirectory, fileName))
      replaced.push(fileName)
    }
  } catch (error) {
    for (const fileName of replaced.reverse()) {
      const targetPath = resolve(dataDirectory, fileName)
      const original = originals.get(fileName)
      if (original) {
        const rollbackPath = `${targetPath}.${randomUUID()}.tmp`
        writeFileSync(rollbackPath, original)
        renameSync(rollbackPath, targetPath)
      }
    }
    throw error
  }
}

function sendJson(res: ServerResponse, statusCode: number, payload: unknown): void {
  res.statusCode = statusCode
  res.setHeader('Content-Type', 'application/json; charset=utf-8')
  res.setHeader('Cache-Control', 'no-store')
  res.end(JSON.stringify(payload))
}

function readRequestBody(req: IncomingMessage): Promise<DataRecord> {
  return new Promise((resolveBody, reject) => {
    const chunks: Buffer[] = []
    let size = 0

    req.on('data', (chunk: Buffer) => {
      size += chunk.length
      if (size > 1024 * 1024) {
        reject(new Error('Request body is too large.'))
        req.destroy()
        return
      }
      chunks.push(chunk)
    })
    req.on('end', () => {
      try {
        const value: unknown = JSON.parse(Buffer.concat(chunks).toString('utf-8'))
        if (typeof value !== 'object' || value === null || Array.isArray(value)) {
          throw new Error('Request body must be a JSON object.')
        }
        resolveBody(value as DataRecord)
      } catch (error) {
        reject(error)
      }
    })
    req.on('error', reject)
  })
}

function runPaymentService(request: DataRecord): Promise<DataRecord> {
  const windowsPython = resolve(projectDirectory, '.venv', 'Scripts', 'python.exe')
  const unixPython = resolve(projectDirectory, '.venv', 'bin', 'python')
  const pythonExecutable = existsSync(windowsPython)
    ? windowsPython
    : existsSync(unixPython)
      ? unixPython
      : process.env.PYTHON || 'python'

  return new Promise((resolveResult, reject) => {
    const child = spawn(
      pythonExecutable,
      ['-m', 'src.core.payment_api'],
      { cwd: projectDirectory, stdio: ['pipe', 'pipe', 'pipe'] },
    )
    let stdout = ''
    let stderr = ''
    child.stdout.setEncoding('utf-8')
    child.stderr.setEncoding('utf-8')
    child.stdout.on('data', (chunk: string) => { stdout += chunk })
    child.stderr.on('data', (chunk: string) => { stderr += chunk })
    child.on('error', reject)
    child.on('close', (code) => {
      if (code !== 0) {
        reject(new Error(stderr.trim() || `PaymentService exited with code ${code}.`))
        return
      }
      try {
        const response: unknown = JSON.parse(stdout)
        if (typeof response !== 'object' || response === null || Array.isArray(response)) {
          throw new Error('PaymentService returned an invalid response.')
        }
        resolveResult(response as DataRecord)
      } catch (error) {
        reject(error)
      }
    })
    child.stdin.on('error', reject)
    child.stdin.end(JSON.stringify(request))
  })
}

async function handleDataRequest(req: IncomingMessage, res: ServerResponse, next: Next): Promise<void> {
  const url = new URL(req.url ?? '/', 'http://localhost')
  const path = url.pathname

  if (!['/api/menu', '/api/orders', '/api/payments', '/api/tables'].includes(path) && !path.startsWith('/api/orders/')) {
    next()
    return
  }

  try {
    if (path === '/api/menu' && req.method === 'GET') {
      sendJson(res, 200, readRecords('menu.json'))
      return
    }

    if (path === '/api/tables' && req.method === 'GET') {
      sendJson(res, 200, readRecords('tables.json'))
      return
    }

    if (path === '/api/payments' && req.method === 'GET') {
      const payments = readRecords('payments.json').map((payment) => ({
        id: payment.id,
        order_id: payment.order_id,
        table_id: payment.table_id,
        payment_time: payment.payment_time,
        amount_paid: payment.amount_paid,
        amount: payment.amount,
        cashier_name: payment.cashier_name,
        cash_received: payment.cash_received,
        change_due: payment.change_due,
        transaction_code: payment.transaction_code,
        method: payment.method,
        status: payment.status,
      }))
      sendJson(res, 200, payments)
      return
    }

    if (path === '/api/payments' && req.method === 'POST') {
      const body = await readRequestBody(req)
      const result = await runPaymentService(body)
      if (typeof result.status === 'number' && typeof result.error === 'string') {
      sendJson(res, result.status, { error: result.error })
      return
      }
      sendJson(res, 200, result)
      return
    }

    if (path === '/api/orders' && req.method === 'GET') {
      sendJson(res, 200, readRecords('orders.json'))
      return
    }

    if (path === '/api/orders' && req.method === 'POST') {
      const body = await readRequestBody(req)
      if (
        (typeof body.table_id !== 'number' && typeof body.table_id !== 'string') ||
        !Array.isArray(body.items) ||
        body.items.length === 0
      ) {
        sendJson(res, 400, { error: 'A table and at least one order item are required.' })
        return
      }
      const orders = readRecords('orders.json')
      const menu = readRecords('menu.json')
      const tables = readRecords('tables.json')
      const table = tables.find((candidate) => String(candidate.id) === String(body.table_id))
      if (!table) {
        sendJson(res, 400, { error: `Table ${String(body.table_id)} was not found.` })
        return
      }
      if (table.status !== 'AVAILABLE') {
        sendJson(res, 409, { error: `Table ${String(body.table_id)} is not available.` })
        return
      }
      const items: DataRecord[] = []
      for (const input of body.items) {
        if (
          typeof input !== 'object' ||
          input === null ||
          typeof input.menu_item_id !== 'string' ||
          !Number.isInteger(input.quantity) ||
          input.quantity <= 0 ||
          (input.note !== undefined && typeof input.note !== 'string')
        ) {
          sendJson(res, 400, { error: 'Order items must have a menu item ID and a positive integer quantity.' })
          return
        }
        const menuItem = menu.find((candidate) => candidate.id === input.menu_item_id)
        if (!menuItem || menuItem.is_available !== true) {
          sendJson(res, 409, { error: `Menu item ${input.menu_item_id} is unavailable.` })
          return
        }
        const unitPrice = menuItem.price
        const prepTime = menuItem.prep_time
        if (
          typeof unitPrice !== 'number' ||
          !Number.isInteger(unitPrice) ||
          unitPrice < 0 ||
          typeof prepTime !== 'number' ||
          !Number.isInteger(prepTime) ||
          prepTime < 0
        ) {
          throw new Error(`Menu item ${input.menu_item_id} has invalid price or preparation time.`)
        }
        items.push({
          menu_item_id: menuItem.id,
          item_name: menuItem.name,
          unit_price: unitPrice,
          quantity: input.quantity,
          subtotal: unitPrice * input.quantity,
          note: input.note ?? '',
          prep_time: prepTime,
        })
      }
      const date = new Date()
      const datePart = `${date.getFullYear()}${String(date.getMonth() + 1).padStart(2, '0')}${String(date.getDate()).padStart(2, '0')}`
      const prefix = `ORD-${datePart}-`
      const sequence = orders.reduce((max, order) => {
        const match = typeof order.id === 'string' ? order.id.match(new RegExp(`^${prefix}(\\d+)$`)) : null
        return match ? Math.max(max, Number(match[1])) : max
      }, 0) + 1
      const order = {
        id: `${prefix}${String(sequence).padStart(3, '0')}`,
        table_id: body.table_id,
        status: 'PENDING',
        created_at: date.toISOString(),
        updated_at: date.toISOString(),
        items,
        notes: typeof body.notes === 'string' ? body.notes : '',
        discount_amount: 0,
        total_amount: items.reduce((total: number, item: DataRecord) => (
          total + (typeof item.subtotal === 'number' ? item.subtotal : 0)
        ), 0),
        final_amount: items.reduce((total: number, item: DataRecord) => (
          total + (typeof item.subtotal === 'number' ? item.subtotal : 0)
        ), 0),
      }
      table.status = 'OCCUPIED'
      table.current_order_id = order.id
      writeRecordUpdates({ 'orders.json': [...orders, order], 'tables.json': tables })
      sendJson(res, 201, order)
      return
    }

    const statusMatch = path.match(/^\/api\/orders\/([^/]+)\/status$/)
    if (statusMatch && req.method === 'PATCH') {
      const orderId = decodeURIComponent(statusMatch[1])
      const body = await readRequestBody(req)
      const nextStatus = body.status
      if (!['PREPARING', 'SERVED', 'CANCELLED'].includes(String(nextStatus))) {
        sendJson(res, 400, { error: 'Unsupported order status.' })
        return
      }
      const orders = readRecords('orders.json')
      const order = orders.find((candidate) => candidate.id === orderId)
      if (!order) {
        sendJson(res, 404, { error: `Order ${orderId} was not found.` })
        return
      }
      const validTransitions: Record<string, string[]> = {
        PENDING: ['PREPARING', 'CANCELLED'],
        PREPARING: ['SERVED', 'CANCELLED'],
      }
      if (!validTransitions[String(order.status)]?.includes(String(nextStatus))) {
        sendJson(res, 409, { error: `Cannot change order from ${String(order.status)} to ${String(nextStatus)}.` })
        return
      }
      order.status = nextStatus
      order.updated_at = new Date().toISOString()
      const updates: Record<string, DataRecord[]> = { 'orders.json': orders }
      if (nextStatus === 'CANCELLED') {
        const tables = readRecords('tables.json')
        const table = tables.find((candidate) => String(candidate.id) === String(order.table_id))
        if (table && table.current_order_id === order.id) {
          table.status = 'AVAILABLE'
          table.current_order_id = null
          updates['tables.json'] = tables
        }
      }
      writeRecordUpdates(updates)
      sendJson(res, 200, order)
      return
    }

    res.setHeader('Allow', 'GET, POST, PATCH')
    sendJson(res, 405, { error: 'Method not allowed.' })
  } catch (error) {
    sendJson(res, 500, {
      error: error instanceof Error ? error.message : 'Unable to access project data.',
    })
  }
}

function projectDataApi(): Plugin {
  return {
    name: 'project-data-api',
    configResolved(config) {
      projectDirectory = resolve(config.root, '..')
      dataDirectory = resolve(config.root, '..', 'data')
    },
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        void handleDataRequest(req, res, next)
      })
    },
    configurePreviewServer(server) {
      server.middlewares.use((req, res, next) => {
        void handleDataRequest(req, res, next)
      })
    },
  }
}

export default defineConfig({
  plugins: [react(), projectDataApi()],
})
