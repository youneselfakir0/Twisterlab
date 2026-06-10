# TwisterLab Active Directory Agent Sync
# This script synchronizes the AI Agent fleet with the local twisterlab.local domain.

$ErrorActionPreference = "Stop"

# Configuration
$OU_NAME = "AI Agents"
$DOMAIN_DN = (Get-ADDomain).DistinguishedName
$AGENTS_OU = "OU=$OU_NAME,$DOMAIN_DN"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "*        TwisterLab Active Directory Agent Sync          *" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Ensure the OU exists
if (-not (Get-ADOrganizationalUnit -Filter "Name -eq '$OU_NAME'" -ErrorAction SilentlyContinue)) {
    Write-Host "[INFO] Creating Organizational Unit: $AGENTS_OU" -ForegroundColor Yellow
    New-ADOrganizationalUnit -Name $OU_NAME -Path $DOMAIN_DN -Description "Container for TwisterLab AI Agents"
} else {
    Write-Host "[OK] Organizational Unit exists: $AGENTS_OU" -ForegroundColor Green
}

# 2. Get Agents from TwisterLab Registry
Write-Host "[INFO] Fetching agent list from TwisterLab registry..." -ForegroundColor Yellow
$agentsJson = poetry run python scripts/dump_agents.py
$agents = $agentsJson | ConvertFrom-Json

if ($null -eq $agents) {
    Write-Host "[ERROR] Failed to fetch agents from registry." -ForegroundColor Red
    exit 1
}

# 3. Sync each agent to AD
$agentNames = $agents | Get-Member -MemberType NoteProperty | Select-Object -ExpandProperty Name

foreach ($key in $agentNames) {
    $agent = $agents.$key
    
    # SamAccountName limit is 20 characters
    $rawSam = "agent.$($agent.name)"
    if ($rawSam.Length -gt 20) {
        $samAccountName = $rawSam.Substring(0, 20)
    } else {
        $samAccountName = $rawSam
    }
    
    $displayName = "TwisterLab Agent - $($agent.name)"
    $description = $agent.description
    
    # Check if user already exists
    $adUser = Get-ADUser -Filter "SamAccountName -eq '$samAccountName'" -ErrorAction SilentlyContinue
    
    if ($null -eq $adUser) {
        Write-Host "[+] Creating AD User: $samAccountName ($displayName)" -ForegroundColor Green
        
        # Create user with a random complex password
        $password = [System.Web.Security.Membership]::GeneratePassword(16, 2) | ConvertTo-SecureString -AsPlainText -Force
        
        New-ADUser -Name $displayName `
                   -SamAccountName $samAccountName `
                   -UserPrincipalName "$samAccountName@twisterlab.local" `
                   -Path $AGENTS_OU `
                   -AccountPassword $password `
                   -Enabled $true `
                   -Description $description `
                   -DisplayName $displayName `
                   -ChangePasswordAtLogon $false
                   
        Write-Host "    [OK] User created." -ForegroundColor Gray
    } else {
        Write-Host "[~] Agent $samAccountName already exists. Updating metadata..." -ForegroundColor Cyan
        Set-ADUser -Identity $samAccountName -Description $description -DisplayName $displayName
    }
}

Write-Host ""
Write-Host "🚀 Synchronization Complete! $($agentNames.Count) agents processed." -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan
