Attribute VB_Name = "ModuleMailing"

Sub Envoyer_Supports()
    Call EnvoyerMailGlobal("supports")
End Sub

Sub Envoyer_Presence()
    Call EnvoyerMailGlobal("presence")
End Sub

Sub Envoyer_Les_Deux()
    Call EnvoyerMailGlobal("deux")
End Sub

Private Sub EnvoyerMailGlobal(TypeEnvoi As String)
    Dim OutApp As Object
    Dim OutMail As Object
    Dim ws As Worksheet
    Dim lastRow As Long
    Dim i As Long
    Dim dest As String
    Dim nom As String
    Dim theme As String
    Dim dateSem As String
    
    ' Activer le gestionnaire d erreur
    On Error GoTo ErrHandler
    
    Set ws = ThisWorkbook.Sheets("Planning Seminaire")
    lastRow = ws.Cells(ws.Rows.Count, "A").End(xlUp).Row
    
    ' Créer l'application Outlook (doit être installé)
    Set OutApp = CreateObject("Outlook.Application")
    
    ' Boucler sur chaque ligne du tableau (démarre ligne 2 car ligne 1 = en têtes)
    For i = 2 To lastRow
        nom = ws.Cells(i, 5).Value ' Colonne E : Intervenant
        dest = ws.Cells(i, 7).Value ' Colonne G : Contact (Email)
        theme = ws.Cells(i, 4).Value ' Colonne D : Séquence
        dateSem = ws.Cells(i, 2).Value ' Colonne B : Date
        
        If dest <> "" And InStr(dest, "@") > 0 Then
            Set OutMail = OutApp.CreateItem(0)
            
            With OutMail
                .To = dest
                .CC = ""
                .BCC = ""
                
                ' Définir le contenu selon le bouton cliqué
                If TypeEnvoi = "supports" Then
                    .Subject = "RAPPEL : Vos supports de présentation - Séminaire " & dateSem
                    .HTMLBody = "Bonjour <b>" & nom & "</b>,<br><br>" & _
                                "Nous vous rappelons que vous animez la session <i>" & theme & "</i>.<br>" & _
                                "Merci de nous faire parvenir vos supports de présentation au plus vite.<br><br>Cordialement,"
                
                ElseIf TypeEnvoi = "presence" Then
                    .Subject = "CONFIRMATION : Votre présence au Séminaire - " & dateSem
                    .HTMLBody = "Bonjour <b>" & nom & "</b>,<br><br>" & _
                                "Merci de bien vouloir confirmer votre heure d'arrivée pour la séquence <i>" & theme & "</i>.<br><br>Cordialement,"
                
                ElseIf TypeEnvoi = "deux" Then
                    .Subject = "Séminaire " & dateSem & " : Présence et Supports (" & theme & ")"
                    .HTMLBody = "Bonjour <b>" & nom & "</b>,<br><br>" & _
                                "Dans le cadre de votre intervention <i>" & theme & "</i>, merci de nous :<br>" & _
                                "1. Confirmer votre présence et heure d'arrivée.<br>" & _
                                "2. Envoyer vos documents de support.<br><br>Cordialement,"
                End If
                
                .Display ' Remplacer par .Send pour envoyer directement sans voir la fenêtre
            End With
            Set OutMail = Nothing
        End If
    Next i
    
    MsgBox "L'envoi des mails (" & TypeEnvoi & ") a été généré avec succès !", vbInformation
    
CleanUp:
    Set OutApp = Nothing
    Set ws = Nothing
    Exit Sub

ErrHandler:
    MsgBox "Erreur lors de la création du mail : " & Err.Description, vbCritical
    Resume CleanUp
End Sub
