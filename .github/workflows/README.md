# 🚀 VitaLink CI/CD Workflows

Questo repository contiene i workflow GitHub Actions per l'automazione del deployment e testing dell'applicazione VitaLink su AWS.

## 📋 Workflow Disponibili

### 1. 🚀 Deploy VitaLink to AWS (`deploy.yml`)
**Trigger**: Push su `main`/`master`, manual dispatch

**Funzionalità**:
- ✅ Test automatici dell'applicazione
- 🐳 Build e push dell'immagine Docker su ECR
- 🔍 Validazione del template CloudFormation
- 🚀 Deployment dell'infrastruttura su AWS
- 🏥 Health check automatico post-deployment
- 📊 Report di deployment dettagliato

### 2. 🧪 Test VitaLink Application (`test.yml`)
**Trigger**: Push su qualsiasi branch, PR, schedule giornaliero

**Funzionalità**:
- 🎨 Code quality checks (Black, isort, flake8)
- 🔍 Type checking con mypy
- 🧪 Unit test con coverage
- 🐳 Test build Docker
- 🔒 Security scanning (bandit, safety)
- 🔗 Integration test con PostgreSQL
- 📊 Report aggregato dei test

### 3. 🚀 Deploy VitaLink (Staging) (`deploy-staging.yml`)
**Trigger**: Push su `develop`, PR su `develop`

**Funzionalità**:
- 🧪 Test rapidi pre-deployment
- 🚀 Deployment automatico su staging
- 🧪 Test post-deployment su staging
- 💬 Commenti automatici su PR con link staging
- 🧹 Pulizia automatica di immagini vecchie

### 4. 📊 Monitor VitaLink Application (`monitor.yml`)
**Trigger**: Schedule (ogni 15 minuti in orario lavorativo), manual dispatch

**Funzionalità**:
- 🏥 Health check dell'applicazione
- 🚢 Monitoraggio servizi ECS
- 💾 Status check database RDS
- 🔄 Controllo Load Balancer
- 💰 Monitoraggio costi AWS
- 📧 Notifiche su problemi critici

### 5. 🗑️ Cleanup AWS Resources (`cleanup.yml`)
**Trigger**: Manual dispatch only

**Funzionalità**:
- 🧹 Eliminazione sicura degli stack CloudFormation
- 🐳 Pulizia repository ECR
- 🔍 Rilevamento risorse orfane
- ⚠️ Protezioni per risorse critiche
- ✅ Verifica finale della pulizia

## 🔧 Setup dei Secrets

Per utilizzare questi workflow, configura i seguenti secrets nel repository GitHub:

### Secrets Obbligatori
```
AWS_ACCESS_KEY_ID         # AWS Access Key ID
AWS_SECRET_ACCESS_KEY     # AWS Secret Access Key
AWS_SESSION_TOKEN         # AWS Session Token (per AWS Education)
DB_PASSWORD               # Password database produzione
DB_PASSWORD_STAGING       # Password database staging
```

### Come aggiungere i secrets:
1. Vai su **Settings** → **Secrets and variables** → **Actions**
2. Clicca **New repository secret**
3. Aggiungi ciascun secret con il nome esatto mostrato sopra

## 🌍 Configurazione Ambienti

### Produzione
- **Stack**: `VitaLink-Stack`
- **Environment**: `production`
- **Trigger**: Push su `main`/`master`

### Staging  
- **Stack**: `VitaLink-Stack-Staging`
- **Environment**: `staging`
- **Trigger**: Push su `develop`

## 🚀 Come Utilizzare

### Deploy Produzione
1. Pushare codice su `main` o `master`
2. Il workflow `deploy.yml` si avvia automaticamente
3. Monitorare il progresso nella tab **Actions**
4. Controllare il summary per URL e status

### Deploy Staging
1. Pushare codice su `develop`
2. Il workflow `deploy-staging.yml` si avvia automaticamente
3. Per PR, riceverai un commento con il link di staging

### Test Manuali
1. Andare su **Actions** → **Test VitaLink Application**
2. Cliccare **Run workflow**
3. Selezionare il branch desiderato

### Monitoraggio
- Il monitoraggio avviene automaticamente ogni 15 minuti
- Per controlli manuali: **Actions** → **Monitor VitaLink Application** → **Run workflow**

### Pulizia Risorse
1. **Actions** → **Cleanup AWS Resources** → **Run workflow**
2. Specificare:
   - Stack name da eliminare
   - Se pulire anche ECR
   - Se forzare l'eliminazione

## 📊 Monitoraggio e Alerting

### Metriche Monitorate
- 🏥 Application health (`/health` endpoint)
- ⏱️ Response time
- 🚢 ECS service status
- 💾 RDS database status
- 🔄 Load balancer health
- 💰 Costi AWS (quando disponibile)

### Notifiche
- ✅ Summary report per ogni run
- ⚠️ Alert su fallimenti critici
- 📊 Report aggregati nei PR

## 🔐 Sicurezza

### Best Practices Implementate
- 🔒 Secrets management sicuro
- 🛡️ Controlli di accesso IAM limitati
- 🔍 Security scanning automatico
- ⚠️ Protezioni per risorse critiche
- 🧹 Pulizia automatica di risorse temporanee

### Limitazioni AWS Education
- ❌ Cost Explorer limitato
- ❌ Alcuni servizi di monitoring non disponibili
- ⚠️ IAM roles limitati (uso di LabRole)

## 🚨 Troubleshooting

### Errori Comuni

#### "Stack already exists"
- Usa il workflow cleanup per eliminare lo stack esistente
- Oppure usa il flag `force_recreate=true` nel deploy

#### "No changes to deploy"
- Normale quando non ci sono modifiche all'infrastruttura
- L'applicazione viene comunque aggiornata

#### "Health check failed"
- Verifica i log ECS nella console AWS
- Controlla che il database sia disponibile
- Verifica le configurazioni di rete

#### "ECR permission denied"
- Verifica che i secrets AWS siano corretti e aggiornati
- Controlla che il session token sia valido

### Log e Debug
- Tutti i workflow forniscono log dettagliati
- Summary reports includono informazioni di debug
- Usa la console AWS per debugging approfondito

## 📈 Estensioni Future

### Possibili Miglioramenti
- 🔄 Blue/Green deployments
- 📊 Metriche custom CloudWatch
- 🔐 Integrazione con AWS Secrets Manager
- 📧 Notifiche Slack/Teams
- 🧪 Test end-to-end automatici
- 📋 Database migrations automatiche

---

## 📞 Supporto

Per problemi con i workflow:
1. Controllare i log del workflow fallito
2. Verificare la configurazione dei secrets
3. Consultare la documentazione AWS
4. Creare un issue con dettagli del problema

---

*Documentazione aggiornata per VitaLink v1.0*
