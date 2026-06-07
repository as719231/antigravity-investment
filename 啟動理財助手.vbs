' 專屬 AI 股市理財助手 - 一鍵啟動腳本
' 雙擊此檔案即可靜默啟動伺服器並自動開啟瀏覽器

Dim oShell, oFSO, sProjectDir, sPort, sURL

sProjectDir = "C:\Users\as719\Desktop\antigravity-investment"
sPort = "8501"
sURL = "http://localhost:" & sPort

Set oShell = CreateObject("WScript.Shell")
Set oFSO = CreateObject("Scripting.FileSystemObject")

' 檢查 Streamlit 是否已在執行
Dim bRunning
bRunning = False

' 用 netstat 查 8501 port 是否已被佔用
Dim oExec, sOutput
Set oExec = oShell.Exec("cmd /c netstat -an | findstr :" & sPort)
sOutput = oExec.StdOut.ReadAll()
If InStr(sOutput, "LISTENING") > 0 Or InStr(sOutput, ":" & sPort) > 0 Then
    bRunning = True
End If

' 如果還沒啟動，就靜默執行 Streamlit
If Not bRunning Then
    Dim sCmd
    sCmd = "cmd /c cd /d " & Chr(34) & sProjectDir & Chr(34) & " && python -m streamlit run app.py --server.address=0.0.0.0 --server.port=" & sPort & " --server.headless true"
    oShell.Run sCmd, 0, False  ' 0 = 隱藏視窗，False = 不等待完成
    
    ' 等待伺服器啟動（最多 15 秒）
    Dim i
    For i = 1 To 15
        WScript.Sleep 1000
        Set oExec = oShell.Exec("cmd /c netstat -an | findstr :" & sPort)
        sOutput = oExec.StdOut.ReadAll()
        If InStr(sOutput, ":" & sPort) > 0 Then
            bRunning = True
            Exit For
        End If
    Next
    
    ' 再等 2 秒讓頁面完全載入
    WScript.Sleep 2000
End If

' 開啟瀏覽器
oShell.Run sURL, 1, False

Set oShell = Nothing
Set oFSO = Nothing
