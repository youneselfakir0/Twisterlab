# 🔍 EDGESERVER HARDWARE VERIFICATION

**Date**: 6 Février 2026  
**Purpose**: Compatibility check for Phase 1 hardware upgrades  
**Server**: EdgeServer (192.168.0.30)

---

## 📊 CURRENT CONFIGURATION (Confirmed)

### System Information

**Hostname**: `edgeserver.twisterlab.local`  
**OS**: Ubuntu 24.04.3 LTS  
**Kernel**: 6.8.0-88-generic  
**Architecture**: x86_64  
**Uptime**: 75+ days

### CPU & Memory (Confirmed)

**CPU**:
- Architecture: x86_64
- Cores: 4 threads available
- Usage: ~10% avg (excellent headroom)

**Memory**:
- Total: 15.6 GB (16GB)
- Used: ~3.9 GB (25%)
- Available: ~11.7 GB
- **Status**: ✅ Sufficient for Harbor + services

### Storage - Current State (Confirmed)

**Disk Layout**:
```
/dev/mapper/ubuntu--vg-ubuntu--lv
├─ Total: 98GB
├─ Used: 73GB (74%)
├─ Free: 25GB
└─ Mount: /
```

**Storage Type**: LVM on physical volume(s)

**Partitioning**:
- Filesystem: ext4
- Volume Group: ubuntu-vg
- Logical Volume: ubuntu-lv

**Performance**:
- ⚠️ **SLOW** - Docker builds 70+ min (should be 3-5 min)
- Root cause: Likely HDD, not SSD

---

## 🔍 HARDWARE TO VERIFY

### Critical Questions for Phase 1

#### 1. Motherboard & Chipset

**Need to verify**:
- [ ] Motherboard make/model
- [ ] Available M.2 slots (NVMe support?)
- [ ] PCIe lanes available
- [ ] SATA ports available (how many used/free?)

**Commands to run**:
```bash
# Motherboard info
sudo dmidecode -t baseboard

# System info
sudo dmidecode -t system

# PCI devices
lspci | grep -E 'SATA|NVMe|Storage'
```

#### 2. M.2 NVMe Compatibility

**Critical specs**:
- M.2 slot type: 2280 (most common)
- Interface: PCIe 3.0 x4 (or better)
- Protocol: NVMe 1.3+
- Form factor support: M.2 M-key

**Verification**:
```bash
# Check for NVMe controller
lspci | grep NVMe

# Check M.2 support in dmesg
dmesg | grep -i nvme

# BIOS/UEFI check (manual - boot into BIOS)
```

**Likely scenarios**:

| Age | Motherboard | M.2 Support | Recommendation |
|-----|-------------|-------------|----------------|
| **<5 years** | Modern | ✅ Likely has M.2 | Safe to purchase NVMe |
| **5-10 years** | Mid-range | 🟡 Maybe M.2 | Verify first! |
| **>10 years** | Legacy | ❌ Unlikely M.2 | SATA SSD fallback |

#### 3. SATA Availability

**Need to verify**:
- [ ] Number of SATA ports on motherboard
- [ ] Number currently used
- [ ] Number available for new drive

**Commands**:
```bash
# List block devices
lsblk

# SATA controllers
lspci | grep SATA

# Physical drives
ls -l /dev/sd*
```

**Current known**:
- At least 1 SATA drive (system drive)
- Unknown: Total SATA ports

#### 4. Power Supply

**Verify**:
- [ ] Wattage sufficient for additional drive
- [ ] Available SATA power connectors

**Typical requirements**:
- NVMe SSD: 3-7W (powered by M.2 slot)
- 2.5" SATA SSD: 2-5W
- 3.5" SATA HDD: 6-15W

**Action**: Visual inspection of PSU

#### 5. Physical Space

**Verify**:
- [ ] M.2 slot accessible (not blocked by GPU, etc)
- [ ] Drive bay available for SATA drive
- [ ] Cooling adequate

**Action**: Open case, inspect

---

## 🎯 PHASE 1 HARDWARE REQUIREMENTS

### Option A: NVMe SSD + SATA Storage (Optimal)

**If motherboard has M.2 NVMe slot:**

**Shopping List**:
1. **Samsung 970 EVO Plus 512GB NVMe** - $120
   - Interface: M.2 PCIe 3.0 x4
   - Form: 2280
   - Speed: 3,500 MB/s read
   - For: `/var/lib/docker`

2. **WD Blue 500GB HDD/SSD** - $45
   - Interface: SATA III
   - For: General storage expansion

**Total**: $165

**Benefits**:
- ✅ Maximum performance (NVMe)
- ✅ Good storage expansion
- ✅ Cost-effective

### Option B: SATA SSD + SATA Storage (Fallback)

**If NO M.2 slot available:**

**Shopping List**:
1. **Samsung 870 EVO 500GB SATA SSD** - $60
   - Interface: SATA III
   - Form: 2.5"
   - Speed: 560 MB/s read (still 10x+ better than HDD)
   - For: `/var/lib/docker`

2. **WD Blue 500GB HDD** - $45
   - Interface: SATA III  
   - For: Storage expansion

**Total**: $105

**Benefits**:
- ✅ Still much faster than HDD
- ✅ Lower cost
- ✅ Compatible with any system

### Option C: Single SATA SSD (Minimal)

**Budget constrained:**

**Shopping List**:
1. **Crucial MX500 1TB SATA SSD** - $90
   - Interface: SATA III
   - Speed: 560 MB/s
   - Use for: Docker + storage

**Total**: $90

**Benefits**:
- ✅ Single drive simplicity
- ✅ Both speed + capacity
- ✅ Lowest budget

---

## ✅ VERIFICATION CHECKLIST

### Pre-Purchase Verification

Before buying ANY hardware, confirm:

- [ ] **Motherboard model identified**
- [ ] **M.2 slot presence confirmed** (if going NVMe)
- [ ] **SATA ports available** (count: ___)
- [ ] **Power connectors available**
- [ ] **Physical space confirmed**
- [ ] **BIOS supports boot from NVMe** (if using NVMe)

### How to Verify (Step-by-step)

**Step 1: SSH to EdgeServer**
```bash
ssh twister@192.168.0.30
```

**Step 2: Collect system info**
```bash
# Save to file for analysis
sudo dmidecode > ~/hardware-info.txt
lspci > ~/pci-devices.txt
lsblk > ~/block-devices.txt
```

**Step 3: Download to local machine**
```bash
scp twister@192.168.0.30:~/hardware-info.txt .
scp twister@192.168.0.30:~/pci-devices.txt .
scp twister@192.168.0.30:~/block-devices.txt .
```

**Step 4: Analyze**
- Search `hardware-info.txt` for motherboard model
- Google motherboard specs
- Confirm M.2 / SATA availability

**Step 5: Physical inspection** (if possible)
- Open server case
- Count SATA ports
- Look for M.2 slot(s)
- Check cooling

---

## 📋 DECISION MATRIX

| Motherboard Has | Recommended Purchase | Cost | Performance |
|-----------------|---------------------|------|-------------|
| **M.2 NVMe + 1 SATA free** | Option A (NVMe + HDD) | $165 | ⭐⭐⭐⭐⭐ Best |
| **M.2 NVMe + no SATA** | NVMe only | $120 | ⭐⭐⭐⭐ Good |
| **No M.2, 2+ SATA free** | Option B (SATA SSD + HDD) | $105 | ⭐⭐⭐⭐ Good |
| **No M.2, 1 SATA free** | Option C (1TB SATA SSD) | $90 | ⭐⭐⭐ OK |
| **No free slots** | External USB 3.0 SSD | $80 | ⭐⭐ Workable |

---

## 🚨 RISK ASSESSMENT

### Risk 1: No M.2 Slot Available

**Probability**: 30% (older server)  
**Impact**: Medium  
**Mitigation**: Fallback to SATA SSD (still 10x+ faster than HDD)

**Action if true**:
- Purchase SATA SSD instead
- Budget: $60 vs $120 (saves $60)
- Performance: 560MB/s vs 3500MB/s (still huge improvement)

### Risk 2: No Available SATA Ports

**Probability**: 10% (unlikely)  
**Impact**: Medium  
**Mitigation**: SATA expansion card or USB 3.0 external

**Action if true**:
- Option A: Add PCIe SATA controller ($25)
- Option B: Use USB 3.0 external SSD ($80)

### Risk 3: Incompatible Form Factor

**Probability**: 5%  
**Impact**: Low  
**Mitigation**: Return policy on all purchases

**Action if true**:
- Return incorrect drive
- Purchase correct form factor

---

## 📞 NEXT ACTIONS

### Immediate (Before Meeting Feb 11)

1. **Collect Hardware Info** (TODAY)
   ```bash
   ssh twister@192.168.0.30
   sudo dmidecode -t baseboard
   sudo dmidecode -t system
   lspci | grep -E 'SATA|NVMe'
   lsblk
   ```

2. **Physical Inspection** (if accessible)
   - Open EdgeServer case
   - Photo motherboard (for model ID)
   - Count SATA ports
   - Check for M.2 slots

3. **Research Motherboard** (once model known)
   - Google: "[Motherboard Model] specs"
   - Confirm: M.2 support, SATA ports
   - Check: Manual PDF

4. **Update Meeting Doc** (before Feb 11)
   - Add confirmed specs
   - Update shopping list
   - Adjust budget if needed

### During Meeting (Feb 11)

5. **Present Findings**
   - Confirmed hardware capabilities
   - Recommended purchase option
   - Adjusted budget (if needed)

6. **Get Approval**
   - GO: Purchase immediately
   - NO-GO: Defer Phase 1

### Post-Meeting (if GO)

7. **Purchase Hardware** (Day 1-2)
   - Order from Amazon/NewEgg (fast shipping)
   - Verify return policy
   - Track shipment

---

## 📊 SUMMARY TABLE

| Item | Status | Action Needed |
|------|--------|---------------|
| **OS Version** | ✅ Ubuntu 24.04 LTS | None |
| **CPU** | ✅ 4 cores | None |
| **Memory** | ✅ 16GB | None |
| **Current Storage** | ✅ 98GB LVM | None |
| **Motherboard Model** | ❓ **UNKNOWN** | ⚠️ **VERIFY ASAP** |
| **M.2 NVMe Support** | ❓ **UNKNOWN** | ⚠️ **VERIFY ASAP** |
| **SATA Ports Free** | ❓ **UNKNOWN** | ⚠️ **VERIFY ASAP** |
| **Physical Space** | ❓ **UNKNOWN** | ⚠️ Inspect case |

---

## 🎯 RECOMMENDATION

**Priority**: **HIGH** - Verify hardware specs BEFORE Feb 11 meeting

**Timeline**:
- TODAY (Feb 6): Collect hardware info via SSH
- Feb 7-8: Physical inspection (if possible)
- Feb 9-10: Research & finalize shopping list
- Feb 11: Present at meeting

**If specs can't be verified before meeting**:
- Present all 3 options (A, B, C)
- Table final decision until verification
- Schedule quick follow-up after verification

---

**Status**: ⚠️ **PENDING HARDWARE VERIFICATION**

**Next Step**: Run verification commands on EdgeServer NOW

**Commands Ready**:
```bash
ssh twister@192.168.0.30
sudo dmidecode -t baseboard | grep -E 'Manufacturer|Product'
sudo dmidecode -t system | grep -E 'Manufacturer|Product'
lspci | grep -E 'SATA|NVMe|Storage'
lsblk
```

---

**Updated**: 6 Février 2026, 06:35 AM  
**Author**: Antigravity AI  
**Status**: Awaiting Hardware Verification
