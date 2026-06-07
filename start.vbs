' AI Stock Advisor - Silent Launcher
' Double-click to start server and open browser

Dim oShell, sProjectDir, sPort, sURL, sCmd, oExec, sOutput, i, bRunning

sProjectDir = "C:\Users\as719\Desktop\antigravity-investment"
sPort = "8501"
sURL = "http://localhost:" & sPort

Set oShell = CreateObject("WScript.Shell")

' Check if port 8501 is already listening
bRunning = False
Set oExec = oShell.Exec("cmd /c netstat -an")
sOutput = oExec.StdOut.ReadAll()
If InStr(sOutput, ":" & sPort) > 0 Then
    bRunning = True
End If

' Start Streamlit silently if not running
If Not bRunning Then
    sCmd = "cmd /c cd /d " & Chr(34) & sProjectDir & Chr(34) & " && python -m streamlit run app.py --server.port=" & sPort & " --server.headless true"
    oShell.Run sCmd, 0, False

    ' Wait up to 20 seconds for server to start
    For i = 1 To 20
        WScript.Sleep 1000
        Set oExec = oShell.Exec("cmd /c netstat -an")
        sOutput = oExec.StdOut.ReadAll()
        If InStr(sOutput, ":" & sPort) > 0 Then
            bRunning = True
            Exit For
        End If
    Next

    WScript.Sleep 2000
End If

' Open browser
oShell.Run sURL

Set oShell = Nothing
