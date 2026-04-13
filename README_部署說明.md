# 獎懲機器人 Telegram 最終版

這一版已經直接按照你現在的 Google 試算表邏輯做成可部署的 Telegram 機器人。

## 已完成功能

### 1. 查詢權重
- 點擊 `查詢權重`
- 跳出員工名單
- 點擊員工姓名後，顯示：
  - 直推人數
  - 團隊人數
  - 直推權重
  - 團隊權重
  - 直推比例
  - 團隊比例

### 2. 獎金查詢
- 點擊 `獎金查詢`
- 跳出員工名單
- 點擊員工姓名後，顯示：
  - 直推收益
  - 團隊收益
  - 違規扣款
  - 違規次數
  - 實際到手
  - 狀態

### 3. 今日獎池
- 點擊 `今日獎池`
- 直接抓 `設定總覽!B18` 的公告文字
- 也就是你試算表中自動組出來的：
  - 今日獎池已更新
  - 直推獎池本日新增 / 本月總額 / 本日開放比例 / 本月可發放總額
  - 團隊獎池本日新增 / 本月總額 / 本日開放比例 / 本月可發放總額

### 4. 獎池更新（管理員）
- 管理員輸入：`獎池更新`
- 或 `/pool_update`
- 機器人會立刻抓最新獎池公告
- 如果有設定 `ANNOUNCE_CHAT_ID`，還會自動同步發到公告群

### 5. 排行榜
- 點擊 `排行榜`
- 依 `排行榜` 工作表顯示前 10 名
- 直接顯示 🥇🥈🥉 或數字排名

### 6. 可選的員工綁定
如果你想讓每個員工只能查自己的資料，可以另外新增一張工作表：

工作表名稱：`Telegram綁定`

欄位格式：

| 員工姓名 | Telegram User ID |
|---|---|
| 明卡 | 123456789 |
| 阿文 | 987654321 |

只要有這張表，機器人就會自動限制綁定用戶只能查自己的資料。

---

## 你的 Google 試算表要保留的工作表名稱
請不要改這些名稱，程式是照這些名字讀：

- `設定總覽`
- `月度計算`
- `排行榜`
- `Telegram綁定`（可選）

---

## 快速部署流程

## 第一步：把 Excel 上傳成 Google 試算表
1. 打開 Google Drive
2. 上傳你之前那份 Excel
3. 用 Google 試算表開啟
4. 確認工作表名稱沒有被改掉

## 第二步：建立 Telegram Bot
1. 打開 Telegram 搜尋 `@BotFather`
2. 輸入 `/newbot`
3. 建立完成後拿到 `Bot Token`

## 第三步：建立 Google Service Account
1. 到 Google Cloud 建立專案
2. 開啟：
   - Google Sheets API
   - Google Drive API
3. 建立 Service Account
4. 建立 JSON Key
5. 把 JSON 內容整段複製到 `.env` 的 `GOOGLE_SERVICE_ACCOUNT_JSON`

## 第四步：把試算表分享給 Service Account
把你的 Google 試算表分享給這個信箱：

`xxxx@your-project-id.iam.gserviceaccount.com`

至少要給「檢視者」權限。

## 第五步：填寫 .env
把 `.env.example` 複製成 `.env`，然後填上：
- `TELEGRAM_BOT_TOKEN`
- `GOOGLE_SHEET_ID`
- `ADMIN_IDS`
- `ANNOUNCE_CHAT_ID`（可不填）
- `GOOGLE_SERVICE_ACCOUNT_JSON`

### Google Sheet ID 在哪裡
假設你的試算表網址是：

`https://docs.google.com/spreadsheets/d/1ABCDEFxxxxxxxxxxxxxxxxxxxx/edit#gid=0`

那 `GOOGLE_SHEET_ID` 就是：

`1ABCDEFxxxxxxxxxxxxxxxxxxxx`

---

## 本機啟動
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.main
```

Windows PowerShell：
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m app.main
```

---

## Railway / Render 部署
啟動指令：
```bash
python -m app.main
```

Python 版本建議：`3.11`

---

## 管理員 ID 怎麼查
1. 先啟動機器人
2. 對機器人發任意訊息
3. 你可以先暫時在程式裡印出 `update.effective_user.id`
4. 拿到數字後填進 `.env` 的 `ADMIN_IDS`

或者直接找 Telegram ID Bot 查自己的 user id。

---

## 目前這版已經能直接配合你的表使用
你平常只需要做這些事：
1. 在 `獎池日報` 輸入每天新增金額與開放比例
2. 在 `員工資料` 更新員工、直推人、違規次數、違規扣款
3. Google Sheets 自動算出 `月度計算`、`排行榜`
4. Telegram 機器人直接讀取這些結果

---

## 目前已對應的獎金邏輯
- 直推最多只算 5 人
- 團隊人數只算直推的直推一層
- 直推比例 = 個人直推權重 / 全員直推權重總和
- 團隊比例 = 個人團隊權重 / 全員團隊權重總和
- 直推收益 = 直推比例 × 直推可發放總額
- 團隊收益 = 團隊比例 × 團隊可發放總額
- 違規 3 次以上，當月獎金清零
- 若收益扣掉違規後變負數，收益與實際到手都顯示 0
- 公司回收金額保留在試算表中可追蹤

---

## 你下一步最適合做的事
1. 先把 Excel 轉成 Google 試算表
2. 建立 Bot Token
3. 建立 Google Service Account
4. 把 `.env` 填好
5. 直接部署到 Railway 或 Render

如果你要更完整下一版，我建議可以加：
- 員工登入綁定流程
- 管理員後台新增違規
- 管理員後台新增每日獎池
- 自動定時每天發排行榜
- 群組內只顯示自己資料，避免互相查看
