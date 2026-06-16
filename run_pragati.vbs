Set WshShell = CreateObject("WScript.Shell")

' Configure paths (VBScript handles backslashes on Windows)
backendPath = "c:\Users\Asus\Documents\sustainable platform\backend"
frontendPath = "c:\Users\Asus\Documents\sustainable platform\frontend\index.html"

' Change working directory to backend
WshShell.CurrentDirectory = backendPath

' Start the FastAPI server silently (0 hides the window, False runs it asynchronously)
WshShell.Run "py -m uvicorn api:app --host 127.0.0.1 --port 8000", 0, False

' Sleep for 3 seconds to let the server start up
WScript.Sleep 3000

' Open the dashboard URL in the default web browser
WshShell.Run "explorer.exe http://127.0.0.1:8000/", 1, False

MsgBox "PRAGATI AI Backend started successfully in the background!" & vbCrLf & _
       "The dashboard has been opened in your browser." & vbCrLf & vbCrLf & _
       "To stop the backend server, please run 'stop_pragati.bat'.", 64, "PRAGATI AI Launcher"
