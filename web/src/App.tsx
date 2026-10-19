import { useEffect, useMemo, useState } from 'react'
import './App.css'

type MenuCategory = string
type OrderStatus = 'PENDING' | 'PREPARING' | 'SERVED' | 'COMPLETED' | 'CANCELLED'
type KitchenStatus = 'Chờ chế biến' | 'Đang nấu' | 'Đã lên món' | 'Đã thanh toán' | 'Đã hủy'

type MenuItem = {
  id: string
  name: string
  category: string
  price: number
  prepMinutes: number
  image: string
  isAvailable: boolean
  featured?: boolean
}

type RawMenuItem = {
  id: string
  name: string
  category: string
  price: number
  prep_time: number
  image: string
  is_available: boolean
}

type RestaurantTable = {
  id: number | string
  name: string
  capacity: number
  status: 'AVAILABLE' | 'OCCUPIED' | 'RESERVED' | string
  current_order_id: string | null
}

type CartEntry = {
  itemId: string
  quantity: number
  note: string
}

type KitchenOrderItem = {
  menuItemId: string
  name: string
  qty: number
  prepMinutes: number
  unitPrice: number
  subtotal: number
  note: string
}

type KitchenOrder = {
  id: string
  table: string
  tableId: string | number
  status: KitchenStatus
  backendStatus: OrderStatus
  finalAmount: number
  estimatedWaitMinutes: number
  items: KitchenOrderItem[]
  createdAt: number
}

type OrderRecord = {
  id: string
  table_id: string | number
  status: OrderStatus
  created_at: string
  updated_at?: string
  items: Array<{
    menu_item_id: string
    item_name: string
    unit_price: number
    quantity: number
    subtotal: number
    note?: string
    prep_time?: number
  }>
  notes?: string
  discount_amount?: number
  total_amount?: number
  final_amount?: number
}

type PaymentRecord = {
  id: string
  order_id: string
  table_id: string | number
  payment_time: string
  amount?: number
  amount_paid: number
  method: 'CASH' | 'BANK_TRANSFER' | 'CARD' | string
  status: 'SUCCESS' | 'FAILED' | 'PENDING' | 'REFUNDED' | string
  cashier_name?: string
  cash_received?: number | null
  change_due?: number
  transaction_code?: string | null
}

const navItems = ['Thực đơn', 'Đơn hàng', 'Lịch sử đơn', 'Bếp', 'Thanh toán', 'Thống kê']

const formatMoney = (value: number) => `${new Intl.NumberFormat('vi-VN').format(value)}đ`

function isPaymentRecord(value: unknown): value is PaymentRecord {
  if (typeof value !== 'object' || value === null) return false
  const record = value as Record<string, unknown>
  return (
    typeof record.id === 'string' &&
    typeof record.order_id === 'string' &&
    (typeof record.table_id === 'string' || typeof record.table_id === 'number') &&
    typeof record.payment_time === 'string' &&
    typeof record.amount_paid === 'number' &&
    (record.cashier_name === undefined || typeof record.cashier_name === 'string') &&
    typeof record.method === 'string' &&
    typeof record.status === 'string'
  )
}

function isPaymentSubmissionResponse(
  value: unknown,
): value is { payment: { status: string; change_due?: number }; invoice: { id: string } | null } {
  if (typeof value !== 'object' || value === null) return false
  const response = value as Record<string, unknown>
  if (typeof response.payment !== 'object' || response.payment === null) return false
  const payment = response.payment as Record<string, unknown>
  if (typeof payment.status !== 'string') return false
  if (payment.change_due !== undefined && typeof payment.change_due !== 'number') return false
  if (response.invoice === null) return true
  if (typeof response.invoice !== 'object') return false
  return typeof (response.invoice as Record<string, unknown>).id === 'string'
}

function isOrderRecord(value: unknown): value is OrderRecord {
  if (typeof value !== 'object' || value === null) return false
  const order = value as Record<string, unknown>
  return (
    typeof order.id === 'string' &&
    (typeof order.table_id === 'number' || typeof order.table_id === 'string') &&
    typeof order.status === 'string' &&
    ['PENDING', 'PREPARING', 'SERVED', 'COMPLETED', 'CANCELLED'].includes(order.status) &&
    typeof order.created_at === 'string' &&
    Array.isArray(order.items) &&
    order.items.every((item) => (
      typeof item === 'object' &&
      item !== null &&
      typeof item.menu_item_id === 'string' &&
      typeof item.item_name === 'string' &&
      typeof item.unit_price === 'number' &&
      typeof item.quantity === 'number' &&
      typeof item.subtotal === 'number'
    ))
  )
}

function isMenuItem(value: unknown): value is RawMenuItem {
  if (typeof value !== 'object' || value === null) return false
  const item = value as Record<string, unknown>
  return (
    typeof item.id === 'string' &&
    typeof item.name === 'string' &&
    typeof item.category === 'string' &&
    typeof item.price === 'number' &&
    typeof item.prep_time === 'number' &&
    typeof item.image === 'string' &&
    typeof item.is_available === 'boolean'
  )
}

function isRestaurantTable(value: unknown): value is RestaurantTable {
  if (typeof value !== 'object' || value === null) return false
  const table = value as Record<string, unknown>
  return (
    (typeof table.id === 'number' || typeof table.id === 'string') &&
    typeof table.name === 'string' &&
    typeof table.capacity === 'number' &&
    typeof table.status === 'string' &&
    (typeof table.current_order_id === 'string' || table.current_order_id === null)
  )
}

function toKitchenOrders(records: OrderRecord[]): KitchenOrder[] {
  const sorted = [...records].sort((a, b) => Date.parse(a.created_at) - Date.parse(b.created_at))
  const statusLabels: Record<OrderStatus, KitchenStatus> = {
    PENDING: 'Chờ chế biến',
    PREPARING: 'Đang nấu',
    SERVED: 'Đã lên món',
    COMPLETED: 'Đã thanh toán',
    CANCELLED: 'Đã hủy',
  }
  let queuedPrepMinutes = 0
  const orders = sorted.map((record) => {
    const items = record.items.map((item) => ({
      menuItemId: item.menu_item_id,
      name: item.item_name,
      qty: item.quantity,
      prepMinutes: item.prep_time ?? 0,
      unitPrice: item.unit_price,
      subtotal: item.subtotal,
      note: item.note ?? '',
    }))
    const prepMinutes = items.reduce((sum, item) => sum + item.qty * item.prepMinutes, 0)
    const estimatedWaitMinutes = record.status === 'PENDING' || record.status === 'PREPARING'
      ? queuedPrepMinutes + prepMinutes
      : 0
    if (record.status === 'PENDING' || record.status === 'PREPARING') {
      queuedPrepMinutes += prepMinutes
    }

    return {
      id: record.id,
      table: typeof record.table_id === 'number' || /^\d+$/.test(record.table_id)
        ? `Bàn ${record.table_id}`
        : record.table_id,
      tableId: record.table_id,
      status: statusLabels[record.status],
      backendStatus: record.status,
      finalAmount: record.final_amount ?? record.total_amount ?? items.reduce((sum, item) => sum + item.subtotal, 0),
      estimatedWaitMinutes,
      items,
      createdAt: Date.parse(record.created_at),
    }
  })
  return orders.reverse()
}

function App() {
  const [activeNav, setActiveNav] = useState<string>('Thực đơn')
  const [activeCategory, setActiveCategory] = useState<MenuCategory>('Tất cả')
  const [search, setSearch] = useState('')
  const [menuData, setMenuData] = useState<MenuItem[]>([])
  const [menuError, setMenuError] = useState('')
  const [tables, setTables] = useState<RestaurantTable[]>([])
  const [cart, setCart] = useState<CartEntry[]>(() => {
    const saved = localStorage.getItem('dung-fatfood-cart')
    return saved ? JSON.parse(saved) : []
  })
  const [notes, setNotes] = useState<Record<string, string>>(() => {
    const saved = localStorage.getItem('dung-fatfood-notes')
    return saved ? JSON.parse(saved) : {}
  })
  const [kitchenOrders, setKitchenOrders] = useState<KitchenOrder[]>([])
  const [ordersError, setOrdersError] = useState('')
  const [ordersLoaded, setOrdersLoaded] = useState(false)
  const [selectedTable, setSelectedTable] = useState('2')
  const [cartHistory, setCartHistory] = useState<CartEntry[][]>([])
  const [futureCart, setFutureCart] = useState<CartEntry[][]>([])
  const [paymentHistory, setPaymentHistory] = useState<PaymentRecord[]>([])
  const [paymentHistoryError, setPaymentHistoryError] = useState('')
  const [paymentHistoryLoaded, setPaymentHistoryLoaded] = useState(false)
  const [paymentOrderId, setPaymentOrderId] = useState('')
  const [paymentMethod, setPaymentMethod] = useState<'CASH' | 'BANK_TRANSFER' | 'CARD'>('CASH')
  const [cashierName, setCashierName] = useState('')
  const [cashReceived, setCashReceived] = useState('')
  const [transactionCode, setTransactionCode] = useState('')
  const [transactionSuccessful, setTransactionSuccessful] = useState(false)
  const [paymentError, setPaymentError] = useState('')
  const [paymentNotice, setPaymentNotice] = useState('')
  const [paymentSubmitting, setPaymentSubmitting] = useState(false)
  const categories: MenuCategory[] = useMemo(
    () => ['Tất cả', ...new Set(menuData.map((item) => item.category))],
    [menuData],
  )
  const availableTables = tables.filter((table) => table.status === 'AVAILABLE')

  useEffect(() => {
    localStorage.setItem('dung-fatfood-cart', JSON.stringify(cart))
  }, [cart])

  useEffect(() => {
    localStorage.setItem('dung-fatfood-notes', JSON.stringify(notes))
  }, [notes])

  useEffect(() => {
    let isMounted = true

    const refreshMenu = async () => {
      try {
        const response = await fetch('/api/menu', { cache: 'no-store' })
        if (!response.ok) throw new Error(`Không tải được thực đơn (HTTP ${response.status}).`)
        const data: unknown = await response.json()
        if (!Array.isArray(data) || !data.every(isMenuItem)) {
          throw new Error('Dữ liệu thực đơn không đúng định dạng.')
        }
        if (isMounted) {
          setMenuData(data.map((item) => ({
            id: item.id,
            name: item.name,
            category: item.category,
            price: item.price,
            prepMinutes: item.prep_time,
            image: item.image,
            isAvailable: item.is_available,
          })))
          setMenuError('')
        }
      } catch (error) {
        if (isMounted) setMenuError(error instanceof Error ? error.message : 'Không tải được thực đơn.')
      }
    }

    void refreshMenu()
    const refreshInterval = window.setInterval(() => void refreshMenu(), 5000)
    return () => {
      isMounted = false
      window.clearInterval(refreshInterval)
    }
  }, [])

  useEffect(() => {
    let isMounted = true

    const refreshTables = async () => {
      try {
        const response = await fetch('/api/tables', { cache: 'no-store' })
        if (!response.ok) throw new Error(`Không tải được danh sách bàn (HTTP ${response.status}).`)
        const data: unknown = await response.json()
        if (!Array.isArray(data) || !data.every(isRestaurantTable)) {
          throw new Error('Dữ liệu bàn không đúng định dạng.')
        }
        if (isMounted) {
          setTables(data)
          setSelectedTable((current) => (
            data.some((table) => table.status === 'AVAILABLE' && String(table.id) === current)
              ? current
              : String(data.find((table) => table.status === 'AVAILABLE')?.id ?? '')
          ))
        }
      } catch (error) {
        if (isMounted) setOrdersError(error instanceof Error ? error.message : 'Không tải được danh sách bàn.')
      }
    }

    void refreshTables()
    const refreshInterval = window.setInterval(() => void refreshTables(), 5000)
    return () => {
      isMounted = false
      window.clearInterval(refreshInterval)
    }
  }, [])

  const refreshOrders = async () => {
    const response = await fetch('/api/orders', { cache: 'no-store' })
    if (!response.ok) throw new Error(`Không tải được đơn hàng (HTTP ${response.status}).`)
    const data: unknown = await response.json()
    if (!Array.isArray(data) || !data.every(isOrderRecord)) {
      throw new Error('Dữ liệu đơn hàng không đúng định dạng.')
    }
    setKitchenOrders(toKitchenOrders(data))
    setOrdersError('')
    setOrdersLoaded(true)
  }

  useEffect(() => {
    let isMounted = true
    const loadOrders = async () => {
      try {
        const response = await fetch('/api/orders', { cache: 'no-store' })
        if (!response.ok) throw new Error(`Không tải được đơn hàng (HTTP ${response.status}).`)
        const data: unknown = await response.json()
        if (!Array.isArray(data) || !data.every(isOrderRecord)) {
          throw new Error('Dữ liệu đơn hàng không đúng định dạng.')
        }
        if (isMounted) {
          setKitchenOrders(toKitchenOrders(data))
          setOrdersError('')
          setOrdersLoaded(true)
        }
      } catch (error) {
        if (isMounted) {
          setOrdersError(error instanceof Error ? error.message : 'Không tải được đơn hàng.')
          setOrdersLoaded(true)
        }
      }
    }

    void loadOrders()
    const refreshInterval = window.setInterval(() => void loadOrders(), 5000)
    return () => {
      isMounted = false
      window.clearInterval(refreshInterval)
    }
  }, [])

  useEffect(() => {
    let isMounted = true

    const refreshPaymentHistory = async () => {
      try {
        const response = await fetch('/api/payments', { cache: 'no-store' })
        if (!response.ok) {
          throw new Error(`Không tải được lịch sử thanh toán (HTTP ${response.status}).`)
        }

        const data: unknown = await response.json()
        if (!Array.isArray(data) || !data.every(isPaymentRecord)) {
          throw new Error('Dữ liệu lịch sử thanh toán không đúng định dạng.')
        }

        if (isMounted) {
          setPaymentHistory(data)
          setPaymentHistoryError('')
          setPaymentHistoryLoaded(true)
        }
      } catch (error) {
        if (isMounted) {
          setPaymentHistoryError(error instanceof Error ? error.message : 'Không tải được lịch sử thanh toán.')
          setPaymentHistoryLoaded(true)
        }
      }
    }

    void refreshPaymentHistory()
    const refreshInterval = window.setInterval(() => void refreshPaymentHistory(), 3000)
    window.addEventListener('focus', refreshPaymentHistory)

    return () => {
      isMounted = false
      window.clearInterval(refreshInterval)
      window.removeEventListener('focus', refreshPaymentHistory)
    }
  }, [])

  const menuById = useMemo(() => Object.fromEntries(menuData.map((item) => [item.id, item])), [menuData])

  const visibleMenu = useMemo(() => {
    return menuData.filter((item) => {
      const matchesCategory = activeCategory === 'Tất cả' || item.category === activeCategory
      const query = search.trim().toLowerCase()
      const matchesSearch = !query || item.name.toLowerCase().includes(query) || item.id.toLowerCase().includes(query)
      return matchesCategory && matchesSearch
    })
  }, [activeCategory, menuData, search])

  const subtotal = cart.reduce((sum, entry) => sum + (menuById[entry.itemId]?.price ?? 0) * entry.quantity, 0)
  const total = subtotal

  const advanceKitchenOrder = async (order: KitchenOrder) => {
    const nextStatus = order.backendStatus === 'PENDING'
      ? 'PREPARING'
      : order.backendStatus === 'PREPARING'
        ? 'SERVED'
        : null
    if (!nextStatus) return
    try {
      const response = await fetch(`/api/orders/${encodeURIComponent(order.id)}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: nextStatus }),
      })
      if (!response.ok) {
        const errorData: unknown = await response.json()
        const message = typeof errorData === 'object' && errorData !== null && 'error' in errorData
          ? String(errorData.error)
          : `Không cập nhật được đơn hàng (HTTP ${response.status}).`
        throw new Error(message)
      }
      await refreshOrders()
    } catch (error) {
      setOrdersError(error instanceof Error ? error.message : 'Không cập nhật được trạng thái đơn hàng.')
    }
  }

  const applyCart = (nextCart: CartEntry[]) => {
    setCartHistory((prev) => [...prev, cart].slice(-12))
    setFutureCart([])
    setCart(nextCart)
  }

  const handleUndo = () => {
    if (!cartHistory.length) return
    const previous = cartHistory[cartHistory.length - 1]
    setFutureCart((prev) => [...prev, cart])
    setCartHistory((prev) => prev.slice(0, -1))
    setCart(previous)
  }

  const handleRedo = () => {
    if (!futureCart.length) return
    const next = futureCart[futureCart.length - 1]
    setCartHistory((prev) => [...prev, cart])
    setFutureCart((prev) => prev.slice(0, -1))
    setCart(next)
  }

  const addToCart = (item: MenuItem) => {
    if (!item.isAvailable) return

    const existing = cart.find((entry) => entry.itemId === item.id)
    if (existing) {
      applyCart(
        cart.map((entry) =>
          entry.itemId === item.id ? { ...entry, quantity: entry.quantity + 1 } : entry,
        ),
      )
      return
    }

    applyCart([...cart, { itemId: item.id, quantity: 1, note: notes[item.id] ?? '' }])
  }

  const updateQuantity = (itemId: string, delta: number) => {
    const item = menuById[itemId]
    if (!item?.isAvailable) return

    const nextCart = cart
      .map((entry) => {
        if (entry.itemId !== itemId) return entry
        const nextQty = entry.quantity + delta
        return nextQty > 0 ? { ...entry, quantity: nextQty } : null
      })
      .filter((entry): entry is CartEntry => Boolean(entry))

    applyCart(nextCart)
  }

  const removeFromCart = (itemId: string) => {
    applyCart(cart.filter((entry) => entry.itemId !== itemId))
  }

  const setItemNote = (itemId: string, note: string) => {
    setNotes((prev) => ({ ...prev, [itemId]: note }))
    setCart((prev) => prev.map((entry) => (entry.itemId === itemId ? { ...entry, note } : entry)))
  }

  const confirmOrder = async () => {
    if (!cart.length) return

    const orderItems = cart.map((entry) => {
      const item = menuById[entry.itemId]
      if (!item) throw new Error(`Không tìm thấy món ${entry.itemId} trong thực đơn.`)
      return {
        menu_item_id: item.id,
        item_name: item.name,
        unit_price: item.price,
        quantity: entry.quantity,
        subtotal: item.price * entry.quantity,
        note: entry.note,
        prep_time: item.prepMinutes,
      }
    })

    try {
      if (!selectedTable || !availableTables.some((table) => String(table.id) === selectedTable)) {
        throw new Error('Vui lòng chọn một bàn còn trống.')
      }
      const response = await fetch('/api/orders', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          table_id: Number.isNaN(Number(selectedTable)) ? selectedTable : Number(selectedTable),
          items: orderItems,
          notes: '',
        }),
      },
      )
      if (!response.ok) {
        const errorData: unknown = await response.json()
        const message = typeof errorData === 'object' && errorData !== null && 'error' in errorData
          ? String(errorData.error)
          : `Không lưu được đơn hàng (HTTP ${response.status}).`
        throw new Error(message)
      }
      await refreshOrders()
      setOrdersError('')
      setCart([])
      setCartHistory([])
      setFutureCart([])
      setActiveNav('Đơn hàng')
    } catch (error) {
      setOrdersError(error instanceof Error ? error.message : 'Không thể lưu đơn hàng.')
    }
  }

  const submitPayment = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const order = kitchenOrders.find((candidate) => candidate.id === paymentOrderId)
    if (!order || order.backendStatus !== 'SERVED') {
      setPaymentError('Chỉ có thể thanh toán đơn đã lên món.')
      return
    }
    if (!cashierName.trim()) {
      setPaymentError('Vui lòng nhập tên nhân viên thu ngân.')
      return
    }
    const cashAmount = Number(cashReceived || order.finalAmount)
    if (paymentMethod === 'CASH' && (!Number.isInteger(cashAmount) || cashAmount < order.finalAmount)) {
      setPaymentError('Tiền khách đưa phải là số nguyên và đủ thanh toán.')
      return
    }
    if (paymentMethod !== 'CASH' && !transactionSuccessful) {
      setPaymentError('Vui lòng xác nhận giao dịch đã được cổng thanh toán chấp nhận.')
      return
    }

    setPaymentSubmitting(true)
    setPaymentError('')
    setPaymentNotice('')
    try {
      const response = await fetch('/api/payments', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          order_id: order.id,
          method: paymentMethod,
          cashier_name: cashierName.trim(),
          cash_received: paymentMethod === 'CASH' ? cashAmount : null,
          transaction_code: paymentMethod === 'CASH' ? null : transactionCode.trim() || null,
          transaction_successful: paymentMethod === 'CASH' ? null : transactionSuccessful,
        }),
      })
      const result: unknown = await response.json()
      if (!response.ok) {
        const message = typeof result === 'object' && result !== null && 'error' in result
          ? String(result.error)
          : `Không thể thanh toán (HTTP ${response.status}).`
        throw new Error(message)
      }
      if (!isPaymentSubmissionResponse(result)) {
        throw new Error('Phản hồi thanh toán không đúng định dạng.')
      }

      if (result.payment.status === 'SUCCESS') {
        const invoiceId = result.invoice?.id ?? ''
        setPaymentNotice(
          `Thanh toán thành công${invoiceId ? ` · hóa đơn ${invoiceId}` : ''}${paymentMethod === 'CASH' ? `. Tiền thối lại: ${formatMoney(result.payment.change_due ?? Math.max(0, cashAmount - order.finalAmount))}.` : '.'}`,
        )
      } else {
        setPaymentError('Giao dịch chưa thành công; đơn hàng vẫn chờ thanh toán.')
      }

      await refreshOrders()
      const [paymentsResponse, tablesResponse] = await Promise.all([
        fetch('/api/payments', { cache: 'no-store' }),
        fetch('/api/tables', { cache: 'no-store' }),
      ])
      if (!paymentsResponse.ok || !tablesResponse.ok) {
        throw new Error('Thanh toán đã được ghi nhận nhưng không thể tải lại dữ liệu mới nhất.')
      }
      const payments: unknown = await paymentsResponse.json()
      const refreshedTables: unknown = await tablesResponse.json()
      if (!Array.isArray(payments) || !payments.every(isPaymentRecord) || !Array.isArray(refreshedTables) || !refreshedTables.every(isRestaurantTable)) {
        throw new Error('Dữ liệu sau thanh toán không đúng định dạng.')
      }
      setPaymentHistory(payments)
      setTables(refreshedTables)
      setPaymentOrderId('')
      setCashReceived('')
      setTransactionCode('')
      setTransactionSuccessful(false)
    } catch (error) {
      setPaymentError(error instanceof Error ? error.message : 'Không thể hoàn tất thanh toán.')
    } finally {
      setPaymentSubmitting(false)
    }
  }

  const isKitchenView = activeNav === 'Bếp'
  const isOrdersView = activeNav === 'Đơn hàng'
  const isPaymentView = activeNav === 'Thanh toán'
  const isPaymentHistoryView = activeNav === 'Lịch sử đơn'
  const servedOrders = kitchenOrders.filter((order) => order.backendStatus === 'SERVED')
  const selectedPaymentOrder = servedOrders.find((order) => order.id === paymentOrderId) ?? servedOrders[0]
  const kitchenQueue = kitchenOrders.filter(
    (order) => order.backendStatus === 'PENDING' || order.backendStatus === 'PREPARING',
  )

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">2</div>
          <div>
            <strong>DŨNG FATFOOD</strong>
          </div>
        </div>

        <nav className="sidebar-nav" aria-label="Sidebar navigation">
          {navItems.map((item) => (
            <button
              key={item}
              type="button"
              className={activeNav === item ? 'nav-item active' : 'nav-item'}
              onClick={() => setActiveNav(item)}
            >
              <span>{item}</span>
            </button>
          ))}
        </nav>
      </aside>

      <main className="content-panel">
        {isKitchenView ? (
          <section className="kitchen-page">
            <div className="kitchen-header">
              <h2>Hàng đợi bếp</h2>
            </div>

            {ordersError && <div className="data-error" role="alert">{ordersError}</div>}

            <div className="kitchen-table-wrapper">
              <table className="kitchen-queue-table">
                <thead>
                  <tr>
                    <th>Mã đơn</th>
                    <th>Mã bàn</th>
                    <th>Số lượng món</th>
                    <th>Trạng thái</th>
                    <th>Thời gian chờ</th>
                    <th>Hành động</th>
                  </tr>
                </thead>
                <tbody>
                  {kitchenQueue.map((order) => (
                    <tr key={order.id}>
                      <td>{order.id}</td>
                      <td>{order.table}</td>
                      <td>{order.items.reduce((total, item) => total + item.qty, 0)}</td>
                      <td>
                        <span className={`status-pill ${order.status === 'Đang nấu' ? 'warning' : 'process'}`}>
                          {order.status}
                        </span>
                      </td>
                      <td>{order.estimatedWaitMinutes} phút</td>
                      <td>
                        <button type="button" className="tiny-button" onClick={() => void advanceKitchenOrder(order)}>
                          {order.backendStatus === 'PENDING' ? 'Bắt đầu chế biến' : 'Đã lên món'}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {ordersLoaded && kitchenQueue.length === 0 && (
              <div className="empty-orders">Hàng đợi bếp hiện đang trống.</div>
            )}
          </section>
        ) : isPaymentView ? (
          <section className="orders-page payment-page">
            <div className="kitchen-header">
              <h2>Thanh toán đơn hàng</h2>
            </div>
            {paymentError && <div className="payment-history-error" role="alert">{paymentError}</div>}
            {paymentNotice && <div className="payment-success" role="status">{paymentNotice}</div>}
            {servedOrders.length === 0 ? (
              <div className="empty-orders">Không có đơn đã lên món cần thanh toán.</div>
            ) : selectedPaymentOrder ? (
              <form className="payment-form" onSubmit={(event) => void submitPayment(event)}>
                <label>
                  <span>Đơn đã lên món</span>
                  <select
                    value={selectedPaymentOrder.id}
                    onChange={(event) => {
                      setPaymentOrderId(event.target.value)
                      setCashReceived('')
                    }}
                  >
                    {servedOrders.map((order) => (
                      <option key={order.id} value={order.id}>
                        {order.id} · {order.table} · {formatMoney(order.finalAmount)}
                      </option>
                    ))}
                  </select>
                </label>
                <div className="payment-due">
                  <span>Số tiền cần thanh toán</span>
                  <strong>{formatMoney(selectedPaymentOrder.finalAmount)}</strong>
                </div>
                <label>
                  <span>Phương thức thanh toán</span>
                  <select
                    value={paymentMethod}
                    onChange={(event) => setPaymentMethod(event.target.value as 'CASH' | 'BANK_TRANSFER' | 'CARD')}
                  >
                    <option value="CASH">Tiền mặt</option>
                    <option value="BANK_TRANSFER">Chuyển khoản</option>
                    <option value="CARD">Thẻ</option>
                  </select>
                </label>
                <label>
                  <span>Tên nhân viên thu ngân</span>
                  <input
                    required
                    value={cashierName}
                    onChange={(event) => setCashierName(event.target.value)}
                    placeholder="Nhập tên nhân viên"
                  />
                </label>
                {paymentMethod === 'CASH' ? (
                  <label>
                    <span>Số tiền khách đưa (VNĐ)</span>
                    <input
                      type="number"
                      min={selectedPaymentOrder.finalAmount}
                      step="1000"
                      required
                      value={cashReceived || String(selectedPaymentOrder.finalAmount)}
                      onChange={(event) => setCashReceived(event.target.value)}
                      placeholder={String(selectedPaymentOrder.finalAmount)}
                    />
                  </label>
                ) : (
                  <>
                    <label>
                      <span>Mã giao dịch</span>
                      <input
                        value={transactionCode}
                        onChange={(event) => setTransactionCode(event.target.value)}
                        placeholder="Nhập mã giao dịch (nếu có)"
                      />
                    </label>
                    <label className="payment-confirm">
                      <input
                        type="checkbox"
                        checked={transactionSuccessful}
                        onChange={(event) => setTransactionSuccessful(event.target.checked)}
                      />
                      <span>Đã xác nhận giao dịch thành công</span>
                    </label>
                  </>
                )}
                <button className="primary-button full-width" type="submit" disabled={paymentSubmitting}>
                  {paymentSubmitting ? 'Đang xử lý...' : 'Xác nhận thanh toán'}
                </button>
              </form>
            ) : null}
          </section>
        ) : isPaymentHistoryView ? (
          <section className="orders-page">
            <div className="kitchen-header">
              <h2>Lịch sử thanh toán</h2>
            </div>

            {paymentHistoryError && (
              <div className="payment-history-error" role="alert">
                {paymentHistoryError}
              </div>
            )}

            {paymentHistory.length === 0 ? (
              <div className="empty-orders">
                {paymentHistoryLoaded ? 'Chưa có giao dịch thanh toán.' : 'Đang tải lịch sử thanh toán...'}
              </div>
            ) : (
              <div className="kitchen-table-wrapper">
                <table className="kitchen-queue-table">
                  <thead>
                    <tr>
                      <th>Mã giao dịch</th>
                      <th>Mã đơn</th>
                      <th>Bàn</th>
                      <th>Thời gian thanh toán</th>
                      <th>Số tiền</th>
                      <th>Nhân viên thu ngân</th>
                      <th>Phương thức</th>
                      <th>Trạng thái</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[...paymentHistory]
                      .sort((a, b) => Date.parse(b.payment_time) - Date.parse(a.payment_time))
                      .map((payment) => (
                        <tr key={payment.id}>
                          <td>{payment.id}</td>
                          <td>{payment.order_id}</td>
                          <td>{payment.table_id}</td>
                          <td>{new Date(payment.payment_time).toLocaleString('vi-VN')}</td>
                          <td>{formatMoney(payment.amount_paid)}</td>
                          <td>{payment.cashier_name || '—'}</td>
                          <td>
                            {payment.method === 'BANK_TRANSFER'
                              ? 'Chuyển khoản'
                              : payment.method === 'CASH'
                                ? 'Tiền mặt'
                                : payment.method === 'CARD'
                                  ? 'Thẻ'
                                  : payment.method}
                          </td>
                          <td>
                            <span className={`status-pill ${payment.status === 'SUCCESS' ? 'success' : payment.status === 'FAILED' ? 'warning' : 'process'}`}>
                              {payment.status === 'SUCCESS'
                                ? 'Thành công'
                                : payment.status === 'FAILED'
                                  ? 'Thất bại'
                                  : payment.status === 'REFUNDED'
                                    ? 'Đã hoàn tiền'
                                    : 'Đang xử lý'}
                            </span>
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        ) : isOrdersView ? (
          <section className="orders-page">
            <div className="kitchen-header">
              <h2>Đơn hàng</h2>
            </div>

            {ordersError && <div className="data-error" role="alert">{ordersError}</div>}

            {kitchenOrders.length === 0 ? (
              <div className="empty-orders">
                {ordersLoaded ? 'Chưa có đơn hàng nào. Hãy chọn món và xác nhận đơn.' : 'Đang tải đơn hàng...'}
              </div>
            ) : (
              <div className="kitchen-table-wrapper">
                <table className="kitchen-queue-table">
                  <thead>
                    <tr>
                      <th>Mã đơn</th>
                      <th>Mã bàn</th>
                      <th>Món đã đặt</th>
                      <th>Trạng thái</th>
                      <th>Thời gian chờ dự kiến</th>
                    </tr>
                  </thead>
                  <tbody>
                    {kitchenOrders.map((order) => (
                      <tr key={order.id}>
                        <td>{order.id}</td>
                        <td>{order.table}</td>
                        <td>{order.items.map((item) => `${item.name} × ${item.qty}`).join(', ')}</td>
                        <td>
                          <span className={`status-pill ${order.backendStatus === 'SERVED' || order.backendStatus === 'COMPLETED' ? 'success' : order.backendStatus === 'CANCELLED' ? 'warning' : order.backendStatus === 'PREPARING' ? 'warning' : 'process'}`}>
                            {order.status}
                          </span>
                        </td>
                        <td>{order.backendStatus === 'PENDING' || order.backendStatus === 'PREPARING' ? `${order.estimatedWaitMinutes} phút` : '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        ) : (
          <>
            <header className="topbar">
              <div>
                <p className="greeting">Xin chào!</p>
                <h1>Chúc bạn có một bữa ăn ngon miệng!</h1>
              </div>

              <div className="topbar-tools">
                <label className="search-box" aria-label="Tìm món ăn">
                  <span>⌕</span>
                  <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Tìm món ăn theo tên hoặc mã món" />
                </label>
              </div>
            </header>

            <section className="hero-banner">
              <div>
                <div className="chip">ƯU ĐÃI HÔM NAY</div>
                <h2>Món ngon – Giá tốt – Thỏa vị</h2>
                <p>Khuyến mãi đặc biệt cho combo gia đình và món mới mỗi ngày.</p>
                <button type="button" className="primary-button" onClick={() => setActiveNav('Thực đơn')}>
                  Đặt món ngay
                </button>
              </div>
              <img src="https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=1200&q=80" alt="Tổng quan DŨNG FATFOOD" />
            </section>

            <section className="menu-layout">
              <div className="menu-column">
                <div className="section-header">
                  <h3>Danh mục món ăn</h3>
                </div>

                {menuError && <div className="data-error" role="alert">{menuError}</div>}
                {ordersError && <div className="data-error" role="alert">{ordersError}</div>}

                <div className="category-row">
                  {categories.map((category) => (
                    <button
                      key={category}
                      type="button"
                      className={activeCategory === category ? 'category-pill active' : 'category-pill'}
                      onClick={() => setActiveCategory(category)}
                    >
                      {category}
                    </button>
                  ))}
                </div>

                <div className="menu-grid">
                  {visibleMenu.map((item) => (
                    <article key={item.id} className="menu-card">
                      <img src={item.image} alt={item.name} />
                      <div className="card-body">
                        <div className="food-meta">
                          <span className="tag">{item.category}</span>
                          <span className={`status-badge ${item.isAvailable ? 'in-stock' : 'out-of-stock'}`}>
                            {item.isAvailable ? 'Còn hàng' : 'Hết hàng'}
                          </span>
                        </div>
                        <h4>{item.name}</h4>
                        <div className="meta-row">
                          <span>{formatMoney(item.price)}</span>
                          <span>{item.prepMinutes} phút</span>
                        </div>
                        <button
                          type="button"
                          className="add-button"
                          onClick={() => addToCart(item)}
                          disabled={!item.isAvailable}
                        >
                          {item.isAvailable ? 'Thêm vào giỏ' : 'Hết hàng'}
                        </button>
                      </div>
                    </article>
                  ))}
                </div>
              </div>

              <aside className="cart-panel">
                <div className="section-header cart-header">
                  <h3>Giỏ hàng của bạn</h3>
                </div>

                {cart.length === 0 ? (
                  <div className="empty-cart">
                    <p>Giỏ hàng đang trống</p>
                    <small>Hãy chọn món để bắt đầu đặt hàng.</small>
                  </div>
                ) : (
                  <div className="cart-list">
                    {cart.map((entry) => {
                      const item = menuById[entry.itemId]
                      if (!item) return null

                      return (
                        <div key={entry.itemId} className="cart-item">
                          <img src={item.image} alt={item.name} />
                          <div className="cart-item-info">
                            <strong>{item.name}</strong>
                            <small>{formatMoney(item.price)}</small>
                            <div className="qty-controls">
                              <button type="button" onClick={() => updateQuantity(entry.itemId, -1)}>-</button>
                              <span>{entry.quantity}</span>
                              <button type="button" onClick={() => updateQuantity(entry.itemId, 1)}>+</button>
                            </div>
                            <textarea
                              value={entry.note}
                              onChange={(event) => setItemNote(entry.itemId, event.target.value)}
                              placeholder="Ghi chú món ăn"
                              rows={2}
                            />
                          </div>
                          <button type="button" className="remove-item" onClick={() => removeFromCart(entry.itemId)}>
                            ×
                          </button>
                        </div>
                      )
                    })}
                  </div>
                )}

                <div className="cart-actions">
                  <button type="button" className="ghost-button" onClick={handleUndo} disabled={!cartHistory.length}>Hoàn tác</button>
                  <button type="button" className="ghost-button" onClick={handleRedo} disabled={!futureCart.length}>Làm lại</button>
                </div>

                <div className="totals-box">
                  <div><span>Tạm tính</span><strong>{formatMoney(subtotal)}</strong></div>
                  <div className="total-line"><span>Tổng tiền</span><strong>{formatMoney(total)}</strong></div>
                </div>

                <label className="table-picker">
                  <span>Chọn bàn</span>
                  <select value={selectedTable} onChange={(event) => setSelectedTable(event.target.value)}>
                    {availableTables.map((table) => (
                      <option key={table.id} value={table.id}>{table.name} · {table.capacity} chỗ</option>
                    ))}
                  </select>
                </label>

                <button
                  type="button"
                  className="primary-button full-width"
                  onClick={() => void confirmOrder()}
                  disabled={!cart.length || !availableTables.length}
                >
                  Xác nhận đơn
                </button>
              </aside>
            </section>

          </>
        )}
      </main>
    </div>
  )
}

export default App
