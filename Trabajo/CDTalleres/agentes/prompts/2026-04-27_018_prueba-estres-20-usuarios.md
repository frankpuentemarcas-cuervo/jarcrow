---
fecha: 2026-04-27
agente_id: "018"
descripcion: "prueba-estres-final-20-usuarios-doctypes-modificados"
proyecto: "CDTalleres"
ia_destino: antigravity
tipo: validacion-carga
estado: completado
archivo_salida: "c:\\jarcrow\\Trabajo\\CDTalleres\\agentes\\respuestas\\2026-04-27_018_prueba-estres-20-usuarios.md"
---

# PRUEBA ESTRÉS FINAL — 20 Usuarios Concurrentes

## 🎯 Objetivo

Validar que autoname='hash' + before_insert scripts + Client Scripts funcionan correctamente bajo carga (20 usuarios simultáneos creando documentos en 5 doctypes modificados).

---

## 📋 Tareas de Validación

### T1 — Setup: Crear 20 usuarios test en Frappe

```bash
ssh -i ~/.ssh/cdtalleres_frontend root@164.92.94.47 '

echo "=== Crear 20 usuarios test ===" 
cd /home/erpnext/frappe-bench

# Crear usuarios stresstest_001 a stresstest_020
for i in {1..20}; do
  USER="stresstest_$(printf "%03d" $i)@cdtalleres.local"
  bench --site CDTALLERES console << EOF
frappe.get_doc({
    "doctype": "User",
    "email": "$USER",
    "first_name": "StressTest",
    "last_name": "$i",
    "user_type": "System User",
    "roles": [{"role": "Accounts User"}]
}).insert(ignore_permissions=True)
print(f"✅ Usuario {$i} creado")
EOF
done

echo ""
echo "=== Obtener API keys para stresstest_001 a stresstest_010 ===" 
for i in {1..10}; do
  USER="stresstest_$(printf "%03d" $i)@cdtalleres.local"
  bench --site CDTALLERES console << EOF
user = frappe.get_doc("User", "$USER")
user.api_key = frappe.generate_hash(length=26)
user.api_secret = frappe.generate_hash(length=26)
user.save(ignore_permissions=True)
print(f"API Key: {user.api_key}:{user.api_secret}")
EOF
done

'
```

**Esperado:** 20 usuarios creados, 10 con API keys generadas.

---

### T2 — Verificar autoname='hash' activo en 5 doctypes

```bash
ssh -i ~/.ssh/cdtalleres_frontend root@164.92.94.47 '

echo "=== Confirmar autoname=hash (5 modificados) ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT 
  name as doctype,
  autoname,
  naming_rule,
  CASE WHEN autoname='"'"'hash'"'"' THEN '"'"'✅ HASH'"'"' ELSE '"'"'❌ NO HASH'"'"' END as estado
FROM tabDocType
WHERE name IN (
  '"'"'Purchase Order'"'"',
  '"'"'Purchase Invoice'"'"',
  '"'"'GL Entry'"'"',
  '"'"'Stock Ledger Entry'"'"',
  '"'"'Historial Pagos txt'"'"'
)
ORDER BY name;
" 2>&1

'
```

**Esperado:** Todos 5 muestren `autoname=hash`.

---

### T3 — Verificar before_insert scripts y SEQUENCEs activos

```bash
ssh -i ~/.ssh/cdtalleres_frontend root@164.92.94.47 '

echo "=== Listar Server Scripts before_insert ===" 
cd /home/erpnext/frappe-bench
bench --site CDTALLERES console << EOF
scripts = frappe.get_list("Server Script", 
    filters={"event": "before_insert", "disabled": 0},
    fields=["name", "doc_type", "event"]
)
for s in scripts:
    print(f"✅ {s.doc_type}: {s.name}")
EOF

echo ""
echo "=== Verificar SEQUENCEs en BD ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT 
  sequence_name,
  NEXT_VALUE as next_id,
  INCREMENT
FROM information_schema.SEQUENCES
WHERE sequence_name LIKE '"'"'seq_%'"'"'
ORDER BY sequence_name;
" 2>&1

'
```

**Esperado:** 5 Server Scripts visibles (CDT-PO-Seq, CDT-PI-Seq, CDT-GLE-Seq, CDT-SLE-Seq, CDT-HPT-Seq), 5 SEQUENCEs (seq_purchase_order, seq_purchase_invoice, seq_gl_entry, seq_stock_ledger, seq_historial_pagos_txt).

---

### T4 — Preparar script Python: generador de carga concurrente

```bash
cat > /tmp/stress_test_cdtalleres.py << 'PYTHON_EOF'
#!/usr/bin/env python3

import requests
import concurrent.futures
import time
import json
from datetime import datetime, timedelta
import statistics

# Configuración
BACKEND_URL = "http://10.124.0.9:8000"  # Backend interno
API_ENDPOINT = "/api/resource"

# Usuarios (stresstest_001 a stresstest_020) — asignar keys T1
USERS = {
    "stresstest_001": "API_KEY_1:API_SECRET_1",
    "stresstest_002": "API_KEY_2:API_SECRET_2",
    # ... continuar hasta stresstest_020
    # (Obtener keys reales de T1)
}

DOCTYPES = [
    "Purchase Order",
    "Purchase Invoice",
    "GL Entry",
    "Stock Ledger Entry",
    "Historial Pagos txt"
]

DOCTYPE_TEMPLATES = {
    "Purchase Order": {
        "doctype": "Purchase Order",
        "supplier": "Test Supplier",
        "currency": "USD",
        "items": [{"item_code": "TEST-001", "qty": 1, "rate": 100}]
    },
    "Purchase Invoice": {
        "doctype": "Purchase Invoice",
        "supplier": "Test Supplier",
        "currency": "USD",
        "items": [{"item_code": "TEST-001", "qty": 1, "rate": 100}]
    },
    "GL Entry": {
        "doctype": "GL Entry",
        "company": "CDTALLERES",
        "posting_date": datetime.now().date().isoformat(),
        "account": "5000 - Expenses - CDTALLERES",
        "debit_in_account_currency": 100,
        "credit_in_account_currency": 0
    },
    "Stock Ledger Entry": {
        "doctype": "Stock Ledger Entry",
        "item_code": "TEST-001",
        "warehouse": "WH-01 - CDTALLERES",
        "posting_date": datetime.now().date().isoformat(),
        "qty_after_transaction": 10,
        "valuation_rate": 100
    },
    "Historial Pagos txt": {
        "doctype": "Historial Pagos txt",
        "usuario": "Test User",
        "fecha": datetime.now().date().isoformat()
    }
}

results = {
    "total_requests": 0,
    "successful": 0,
    "failed": 0,
    "errors": {},
    "latencies": [],
    "doctypes_created": {}
}

def make_request(user_idx, doctype):
    """Crear documento como usuario test"""
    user_email = f"stresstest_{user_idx:03d}@cdtalleres.local"
    
    # Buscar API key (simulada — T1 proporciona keys reales)
    api_key = USERS.get(f"stresstest_{user_idx:03d}", "FAKE_KEY")
    
    if ":" not in api_key:
        return {
            "user": user_email,
            "doctype": doctype,
            "status": "error",
            "error": "API key not found",
            "latency_ms": 0
        }
    
    headers = {
        "Authorization": f"token {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = json.dumps(DOCTYPE_TEMPLATES[doctype])
    
    start = time.time()
    try:
        resp = requests.post(
            f"{BACKEND_URL}{API_ENDPOINT}/{doctype}",
            headers=headers,
            data=payload,
            timeout=10
        )
        latency_ms = (time.time() - start) * 1000
        
        if resp.status_code in [200, 201]:
            doc = resp.json().get("data", {})
            return {
                "user": user_email,
                "doctype": doctype,
                "status": "success",
                "name": doc.get("name"),
                "latency_ms": latency_ms
            }
        else:
            return {
                "user": user_email,
                "doctype": doctype,
                "status": "error",
                "error": f"HTTP {resp.status_code}: {resp.text[:200]}",
                "latency_ms": latency_ms
            }
    except Exception as e:
        latency_ms = (time.time() - start) * 1000
        return {
            "user": user_email,
            "doctype": doctype,
            "status": "error",
            "error": str(e),
            "latency_ms": latency_ms
        }

def run_stress_test():
    """Ejecutar prueba: 20 usuarios × 5 doctypes = 100 requests concurrentes"""
    print(f"\n🚀 INICIANDO PRUEBA ESTRÉS — {datetime.now().isoformat()}")
    print(f"   Configuración: 20 usuarios × 5 doctypes = 100 requests\n")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = []
        
        # Distribuir: cada usuario crea documento en cada doctype
        for user_idx in range(1, 21):
            for doctype in DOCTYPES:
                future = executor.submit(make_request, user_idx, doctype)
                futures.append(future)
        
        # Recolectar resultados
        for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
            result = future.result()
            
            results["total_requests"] += 1
            
            if result["status"] == "success":
                results["successful"] += 1
                results["latencies"].append(result["latency_ms"])
                doctype = result["doctype"]
                if doctype not in results["doctypes_created"]:
                    results["doctypes_created"][doctype] = []
                results["doctypes_created"][doctype].append(result["name"])
                print(f"  ✅ {result['user']} → {result['doctype']}: {result['name']} ({result['latency_ms']:.1f}ms)")
            else:
                results["failed"] += 1
                error = result["error"]
                if error not in results["errors"]:
                    results["errors"][error] = 0
                results["errors"][error] += 1
                print(f"  ❌ {result['user']} → {result['doctype']}: {error}")
    
    return results

def print_summary(results):
    """Imprimir resumen ejecutivo"""
    print(f"\n{'='*70}")
    print(f"📊 RESUMEN ESTRÉS — {datetime.now().isoformat()}")
    print(f"{'='*70}\n")
    
    print(f"Total requests: {results['total_requests']}")
    print(f"Exitosos: {results['successful']} ({100*results['successful']/results['total_requests']:.1f}%)")
    print(f"Fallidos: {results['failed']} ({100*results['failed']/results['total_requests']:.1f}%)")
    
    if results["latencies"]:
        latencies = results["latencies"]
        print(f"\nLatencias (ms):")
        print(f"  Min: {min(latencies):.1f}")
        print(f"  Max: {max(latencies):.1f}")
        print(f"  Promedio: {statistics.mean(latencies):.1f}")
        print(f"  Mediana: {statistics.median(latencies):.1f}")
        print(f"  P95: {sorted(latencies)[int(0.95*len(latencies))]:.1f}")
        print(f"  P99: {sorted(latencies)[int(0.99*len(latencies))]:.1f}")
    
    print(f"\nDocumentos creados por doctype:")
    for doctype, names in results["doctypes_created"].items():
        print(f"  {doctype}: {len(names)} documentos")
        print(f"    Samples: {names[:3]}")
    
    if results["errors"]:
        print(f"\nErrores:")
        for error, count in results["errors"].items():
            print(f"  {error}: {count} ocurrencias")
    
    print(f"\n{'='*70}\n")

if __name__ == "__main__":
    results = run_stress_test()
    print_summary(results)
    
    # Guardar JSON para análisis
    with open("/tmp/stress_test_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    print("✅ Resultados guardados en /tmp/stress_test_results.json")

PYTHON_EOF

chmod +x /tmp/stress_test_cdtalleres.py
```

---

### T5 — Obtener API keys reales y actualizar script

```bash
ssh -i ~/.ssh/cdtalleres_frontend root@164.92.94.47 '

echo "=== Extraer API keys de 10 usuarios (para script Python) ===" 
cd /home/erpnext/frappe-bench

bench --site CDTALLERES console << EOF
import json
keys = {}
for i in range(1, 11):
    user_email = f"stresstest_{i:03d}@cdtalleres.local"
    try:
        user = frappe.get_doc("User", user_email)
        keys[f"stresstest_{i:03d}"] = f"{user.api_key}:{user.api_secret}"
    except:
        pass

# Guardar en archivo accesible
with open("/tmp/api_keys_stress.json", "w") as f:
    json.dump(keys, f)
print("✅ Keys guardadas en /tmp/api_keys_stress.json")
EOF

cat /tmp/api_keys_stress.json

'
```

---

### T6 — Monitorear recursos backend DURANTE prueba

```bash
ssh -i ~/.ssh/cdtalleres_frontend root@164.92.94.47 '

echo "=== Iniciar monitoreo (correr en terminal aparte) ===" 
# En otra shell SSH, ejecutar esto MIENTRAS corre T7
echo "Monitoreo activo: CPU, memoria, conexiones DB, requests Nginx"
while true; do
  clear
  echo "=== Backend Metrics — $(date) ===" 
  echo ""
  echo "CPU/Memoria:"
  ps aux | grep -E "^root.*python|^root.*gunicorn" | head -5
  echo ""
  echo "Conexiones MariaDB (backend → 10.124.0.7):"
  netstat -an 2>/dev/null | grep "10.124.0.7:3306" | grep ESTABLISHED | wc -l
  echo ""
  echo "Procesos Frappe:"
  pgrep -l python | grep -i frappe | wc -l
  echo ""
  echo "Requests Nginx último 10s:"
  tail -n 20 /var/log/nginx/access.log 2>/dev/null | wc -l
  sleep 2
done

'
```

---

### T7 — Ejecutar prueba estrés

```bash
ssh -i ~/.ssh/cdtalleres_frontend root@164.92.94.47 '

echo "=== Ejecutar stress test (100 requests concurrentes) ===" 
# Asegurarse que API keys en script estén actualizadas (T5)
python3 /tmp/stress_test_cdtalleres.py 2>&1 | tee /tmp/stress_test_$(date +%s).log

'
```

**Esperado:**
- 100 requests totales (20 usuarios × 5 doctypes)
- ≥90% exitosos
- Latencia promedio <2000ms
- Sin errores de autoname
- Documentos creados con format correcto (PO-XXXXX, PI-XXXXX, etc. No hash)

---

### T8 — Verificar documentos creados en BD

```bash
ssh -i ~/.ssh/cdtalleres_frontend root@164.92.94.47 '

echo "=== Contar documentos nuevos por doctype ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT 
  doctype,
  COUNT(*) as count,
  MIN(name) as primer_doc,
  MAX(name) as ultimo_doc
FROM (
  SELECT doctype, name FROM tabPurchase_Order WHERE creation >= DATE_SUB(NOW(), INTERVAL 30 MINUTE)
  UNION ALL
  SELECT doctype, name FROM tabPurchase_Invoice WHERE creation >= DATE_SUB(NOW(), INTERVAL 30 MINUTE)
  UNION ALL
  SELECT doctype, name FROM tabGL_Entry WHERE creation >= DATE_SUB(NOW(), INTERVAL 30 MINUTE)
  UNION ALL
  SELECT doctype, name FROM tabStock_Ledger_Entry WHERE creation >= DATE_SUB(NOW(), INTERVAL 30 MINUTE)
  UNION ALL
  SELECT doctype, name FROM tabHistorial_Pagos_txt WHERE creation >= DATE_SUB(NOW(), INTERVAL 30 MINUTE)
) docs
GROUP BY doctype
ORDER BY doctype;
" 2>&1

'
```

**Verificar:** Nombres siguen formato esperado (NO son hashes):
- Purchase Order: `PO-XXXXX`
- Purchase Invoice: `PI-XXXXX`
- GL Entry: `GLE-XXXXX`
- Stock Ledger Entry: `SLE-XXXXX`
- Historial Pagos txt: `HPT-XXXXX`

---

### T9 — Verificar BD: no hay __newname en documentos nuevos

```bash
ssh -i ~/.ssh/cdtalleres_frontend root@164.92.94.47 '

echo "=== Verificar que __newname NO aparece en datos persistidos ===" 
mysql -h 10.124.0.7 -u root -p".Overskull2026.m" _0646d69b639ad0ff -e "
SELECT 
  COUNT(*) as ocurrencias_newname
FROM (
  SELECT * FROM tabPurchase_Order WHERE name LIKE '"'"'__%'"'"' OR creation >= DATE_SUB(NOW(), INTERVAL 30 MINUTE)
  UNION ALL
  SELECT * FROM tabPurchase_Invoice WHERE name LIKE '"'"'__%'"'"' OR creation >= DATE_SUB(NOW(), INTERVAL 30 MINUTE)
  UNION ALL
  SELECT * FROM tabGL_Entry WHERE name LIKE '"'"'__%'"'"' OR creation >= DATE_SUB(NOW(), INTERVAL 30 MINUTE)
) all_docs
WHERE name LIKE '"'"'%_newname%'"'"' OR name LIKE '"'"'%__newname%'"'"';
" 2>&1

echo "Expected: 0"

'
```

---

### T10 — Test Client Scripts: cargar forma y verificar JS

```bash
ssh -i ~/.ssh/cdtalleres_frontend root@164.92.94.47 '

echo "=== Verificar Client Scripts CDT-Hide-Newname-* existen ===" 
cd /home/erpnext/frappe-bench

bench --site CDTALLERES console << EOF
scripts = frappe.get_list("Client Script",
    filters={"name": ["like", "%Hide-Newname%"], "disabled": 0},
    fields=["name", "dt", "enabled"]
)
print(f"Client Scripts activos: {len(scripts)}")
for s in scripts:
    print(f"  ✅ {s.name} ({s.dt})")
EOF

'
```

---

### T11 — Test E2E: abrir forma en navegador y verificar __newname oculto

```bash
echo "=== Prueba manual (navegador) ===" 
# Acceder a: https://cdtalleres.shalom.com.pe
# Login: stresstest_001@cdtalleres.local / password
# Navegar a: Nuevo → Purchase Order
# Verificar:
#   1. Formulario carga sin errores
#   2. Campo __newname NO visible en layout
#   3. Cliente Script CDT-Hide-Newname-PO ejecutado (revisar browser console)
#   4. Crear nuevo PO, guardar
#   5. Nombre generado formato: PO-XXXXX (no hash)

echo "PASOS:"
echo "1. Abrir https://cdtalleres.shalom.com.pe"
echo "2. Usar credenciales: stresstest_001@cdtalleres.local / [password de user]"
echo "3. Crear nuevo Purchase Order"
echo "4. Verificar: Sin __newname visible, nombre = PO-XXXXX"
echo "5. Abrir DevTools → Console, buscar: CDT-Hide-Newname ejecutado"
```

---

## 📊 Reporte Obligatorio

Crear: `c:\jarcrow\Trabajo\CDTalleres\agentes\respuestas\2026-04-27_018_prueba-estres-20-usuarios.md`

**Estructura:**

```markdown
# Prueba Estrés Final — 20 Usuarios

## T1: Crear 20 usuarios test + API keys
RESULTADO: [count de usuarios creados]
API keys generados: [count]

## T2: Verificar autoname='hash' en 5 doctypes
ESTADO: [tabla]
✅ Todos tienen autoname=hash: [SI/NO]

## T3: Server Scripts y SEQUENCEs
Scripts before_insert: [count]
SEQUENCEs existentes: [count]

## T4-T5: Script Python + API keys actualizadas
Script ubicación: /tmp/stress_test_cdtalleres.py
API keys: [count preparadas]

## T6: Monitoreo recursos
[Observaciones durante ejecución]
CPU pico: [%]
Memoria pico: [MB]
Conexiones DB simultáneas: [count]

## T7: Resultados estrés
Total requests: 100
Exitosos: [N] ([%])
Fallidos: [N] ([%])
Latencia promedio: [ms]
P95 latencia: [ms]
P99 latencia: [ms]
Throughput: [req/s]

## T8: Documentos creados en BD
[Tabla con counts por doctype]
Primer doc creado: [name]
Último doc creado: [name]
Formato nombres: [PO-XXXXX / PI-XXXXX / etc]

## T9: __newname en datos
Ocurrencias __newname persistidas: 0
ESTADO: ✅ LIMPIO

## T10: Client Scripts activos
Scripts CDT-Hide-Newname: [count]
Todos habilitados: [SI/NO]

## T11: Test E2E (navegador)
Formulario carga sin errores: [SI/NO]
Campo __newname visible: [NO/SI]
Nuevo PO nombre generado: [name]
Formato correcto: [SI/NO]

## CONCLUSIÓN

✅ **PRUEBA EXITOSA:** [SI/NO]

Validaciones pasadas:
- [✅/❌] autoname='hash' activo
- [✅/❌] before_insert scripts ejecutándose
- [✅/❌] SEQUENCE incrementa correctamente
- [✅/❌] 100 documentos creados exitosamente bajo carga
- [✅/❌] Nombres generados formato correcto (NO hash)
- [✅/❌] __newname NO persistido en BD
- [✅/❌] Client Scripts ejecutándose
- [✅/❌] Latencias aceptables (<2000ms promedio)

**Estado final:** [LISTO PRODUCCIÓN / REQUIERE AJUSTES]

Detalles problemas (si aplica): [...]
```

---

## ⚠️ INSTRUCCIONES CRÍTICAS

1. **T1:** Crear 20 usuarios (scripts pueden crear 10, completar resto manualmente si API console lenta)
2. **T1:** Generar + guardar API keys 10 usuarios (suficiente para demostrar carga distribuida)
3. **T2-T3:** Verificar ANTES de estrés
4. **T5:** Actualizar script Python con keys reales de T1
5. **T6:** Correr en terminal SSH APARTE DURANTE T7 (monitoreo paralelo)
7. **T7:** Interpretar resultado: ≥90% éxito = PRUEBA PASADA
8. **T8:** Verificar nombres generados = format correcto
9. **T9:** Crítico — __newname count debe = 0 (confirma fix funcionando)
10. **T11:** Manual en navegador — validar UX + JS ejecución

---

## 🎯 Criterios de Éxito

**PRUEBA PASADA si:**
- ✅ Autoname='hash' en 5 doctypes
- ✅ ≥90 de 100 requests exitosos
- ✅ Latencia promedio <2000ms
- ✅ Todos documentos nombres formato correcto
- ✅ BD conteo __newname = 0
- ✅ Client Scripts activos
- ✅ E2E navegador sin __newname visible

**PRUEBA FALLIDA si:**
- ❌ <90% éxito (timeout, auth errors, DB errors)
- ❌ Latencia >3000ms promedio
- ❌ Nombres generados como hash
- ❌ __newname aparece en BD
- ❌ Client Scripts no ejecutan
- ❌ __newname visible en formulario

Si falla → Crear prompt 019 con diagnosis específico.
