# The Autonomous AI Pentest Agent Tooling Landscape

## Executive summary

This catalog maps **~270 tools, datasets, standards, and commercial products** relevant to building an autonomous AI pentesting agent that scans paid AI agents and MCP servers, settles probe costs in x402 stablecoin, persists learning across scans, and posts EAS attestations on Base Sepolia under an ENS identity.

**Top 10 to integrate first:**
1. **PyRIT** (MIT) — orchestrator/converter/scorer architecture mirrors what you're building; lift Crescendo + TAP + XPIA.
2. **garak** (Apache-2.0) — probe/detector plugin taxonomy with REST target.
3. **Snyk/Invariant mcp-scan** (Apache-2.0) — canonical MCP attacks (tool poisoning, shadowing, rug-pull) ready to weaponize.
4. **Agentic Radar (SplxAI)** (Apache-2.0) — agent-framework-aware static + dynamic scanner; OWASP/MAESTRO mapping table.
5. **FuzzyAI (CyberArk)** (Apache-2.0) — `rest/http.raw` target + 18 attack methods; cleanest match for x402/MCP HTTP shape.
6. **Inspect AI** (MIT, UK AISI) — base eval/agent harness with Docker/k8s sandbox; 200+ pre-built evals.
7. **coinbase/x402 SDK** (Apache-2.0) + **PolicyLayer** (MIT) — payment rail and mandatory spend-cap enforcement.
8. **EAS contracts + SDK** (MIT) — finding attestations on Base Sepolia.
9. **ERC-8004** trustless-agent registries — agent identity + reputation + validation.
10. **Damn Vulnerable MCP Server** (MIT) — drop-in benchmark with 10 graded vulnerability classes.

**Top 5 competitive threats:**
1. **MerchantGuard "Mystery Shopper"** — already runs 10-probe agent certification with x402 paywalls. Closest live analog.
2. **HexStrike AI** — 150+ pentest tools wrapped as MCP server with 12+ specialist agents.
3. **Mindgard** — continuous automated AI red teaming, ATLAS-mapped, $11.6M raised.
4. **zauth** — continuous endpoint verification + RepoScan + automatic refunds; same problem space.
5. **SplxAI / Agentic Radar** — open-source scanner + commercial platform with the same workflow shape.

**Cross-cutting M&A note:** Robust Intelligence → Cisco; Lakera → Check Point; Protect AI → Palo Alto ($700M); Apex → Tenable; CalypsoAI → F5; Prompt Security → SentinelOne; Pangea → CrowdStrike. Independent startups remaining at speed: Mindgard, SplxAI, Patronus, Adversa, TrojAI, Zenity, Noma, WitnessAI, Operant, Straiker, HiddenLayer, Cranium, Knostic, DeepKeep, Aim, Lasso.

---

## 1. LLM red-team and vulnerability scanners

| Name | License | Status | What it does | How to use |
|---|---|---|---|---|
| **garak** (NVIDIA) — github.com/NVIDIA/garak | Apache-2.0 | Active, ~5.5k★ | Plugin probe→generator→detector→evaluator harness; ~50 probes (DAN, encoding, GCG, ATKGEN). | Best architectural reference; subprocess `--target_type rest`; lift probe/detector abstraction wholesale. |
| **PyRIT** (Microsoft) — github.com/microsoft/PyRIT | MIT | Active, ~3.4k★, v0.11 | Multi-turn orchestrator/converter/scorer; built-in Crescendo, TAP, PAIR, XPIA. | Cleanest orchestrator pattern to lift; reuse Crescendo + TAP. |
| **promptfoo** — github.com/promptfoo/promptfoo | MIT | Very active, ~30k★ | HTTP-target red-team CLI; 50+ vuln plugins, 20+ strategies; OWASP/NIST presets. | Wrap as subprocess against x402/MCP endpoints; OWASP framework-mapped. |
| **PurpleLlama / CyberSecEval 1–4** (Meta) — github.com/meta-llama/PurpleLlama | MIT (evals) | Active, ~3k★ | MITRE ATT&CK uplift, insecure-code, prompt-injection (text/visual), autonomous offensive cyber, AutoPatchBench, CyberSOCEval. | Lift PI datasets directly; benchmark autonomous offensive ops. |
| **Giskard** (giskard-oss / v3) — github.com/Giskard-AI/giskard-oss | Apache-2.0 | Active, ~5.2k★ | OS agent eval with 40+ probes; RAGET auto-test-set generation. | Library import for multi-turn adversarial probing. |
| **DeepTeam** (Confident-AI) — github.com/confident-ai/deepteam | Apache-2.0 | Active, ~2k★ | 50+ vulnerabilities + 20+ research-backed attacks; OWASP/NIST/MITRE/Aegis presets. | Library import; lift OWASP-mapped vulnerability taxonomy. |
| **LLM Guard** (Protect AI/Palo Alto) — github.com/protectai/llm-guard | MIT | Active, ~2.5k★ | 15 input + 20 output scanners (deberta-v3 PI model, PII anonymizer, canary). | Reference defender-side competitive landscape; use as self-test that attack succeeded. |
| **NeMo Guardrails** (NVIDIA) — github.com/NVIDIA-NeMo/Guardrails | Apache-2.0 | Active, ~6k★ | Programmable Colang rails; integrates Llama Guard, NemoGuard. | Reference rail pattern — every rail = attack surface to probe. |
| **Llama Guard / Prompt Guard / Code Shield** (Meta) — meta-llama on HF | Llama Community | Active | Safety classifier suite. | Reference defender; bypass tests. |
| **Aegis Content Safety** (NVIDIA) — HF: nvidia/Aegis-AI-Content-Safety | Llama 2 (model) / CC-BY-4.0 (data) | Active, v2.0 | LlamaGuard-based 13-cat classifier + 33k labeled dataset. | Lift 13-category taxonomy; use as content-safety target. |
| **Vigil** (deadbits) — github.com/deadbits/vigil-llm | Apache-2.0 | **Mostly dormant** (Dec 2023) | YARA + transformer + vector-DB + canary + sentiment scoring. | Lift YARA rule library and canary-token architecture. |
| **Rebuff** (Protect AI) — github.com/protectai/rebuff | Apache-2.0 | **Archived** | 4-layer defense (heuristics, LLM, vector-DB, canary). | Reference only; lift canary-word architecture. |
| **Open-Prompt-Injection** (Liu et al., USENIX'24) — github.com/liu00222/Open-Prompt-Injection | MIT | Sporadic | 5 attack strategies × 7 tasks × 10 LLMs × 10 defenses; DataSentinel + PromptLocate. | Lift the 5 canonical attack-strategy primitives. |
| **WhistleBlower** (Repello-AI) — github.com/Repello-AI/whistleblower | MIT | Sporadic, ~600★ | Black-box system-prompt extraction via in-context inference. | Direct lift as recon module against MCP/x402 targets. |
| **promptmap2** (utkusen) — github.com/utkusen/promptmap | MIT (note: GPLv3 in some forks) | Active, ~940★ | YAML rules; black-box HTTP target; Controller-LLM judge. | Wrap as subprocess; lift YAML rule format. |
| **prompt-fuzzer / ps-fuzz** (Prompt Security) — github.com/prompt-security/ps-fuzz | MIT | Sporadic, ~480★ | 15 attack types (AIM, base64, DAN, UCAR, system-prompt-stealer); takes system prompt as input. | Lift attack-class implementations; dynamic-from-system-prompt approach. |
| **Plexiglass** — github.com/safellama/plexiglass | MIT | **Mostly abandoned** | CLI for adversarial testing via litellm. | Reference only. |
| **AI Prompt Fuzzer** (PortSwigger) — github.com/PortSwigger/ai-prompt-fuzzer | MIT | Active, ~200★ | Burp Suite extension; v3 has AI-vs-AI mode. | Reference HTTP-replay attack pattern. |
| **LLMFuzzer** (mnns) | MIT | **Abandoned** (late 2023), ~290★ | First fuzzing framework for LLM HTTP-API integrations via YAML config. | Reference only. |
| **FuzzyAI** (CyberArk) — github.com/cyberark/FuzzyAI | Apache-2.0 | Active, ~1.2k★ | 18+ attacks (ASCII smuggling, Crescendo, ActorAttack, GA, ArtPrompt, BoN, PAP); `rest/http.raw` raw-HTTP-file targets. | **Highest leverage** — `rest/http.raw` matches MCP/x402; lift attacks as Python modules. |
| **GPTFuzz / GPTFuzzer** (sherdencooper) — github.com/sherdencooper/GPTFuzz | MIT | Sporadic, ~580★ | AFL-inspired mutator over 76 jailbreak templates; MCTS seed-selection; RoBERTa judge. | Lift mutator+MCTS as inner search loop. |
| **EasyJailbreak** — github.com/EasyJailbreak/EasyJailbreak | **GPL-3.0** | Sporadic, ~720★ | Unified Selector/Mutator/Constraint/Evaluator with GPTFuzzer/PAIR/TAP/ReNeLLM/Multilingual/Jailbroken recipes. | **GPL caution**; lift attack recipes individually. |
| **JailbreakBench** — github.com/JailbreakBench/jailbreakbench | MIT | Active, ~750★ | NeurIPS'24 benchmark: 100 harmful + 100 benign; SmoothLLM defense. | Lift JBB-Behaviors as baseline corpus. |
| **JailbreakEval** (ThuCCSLab) — github.com/ThuCCSLab/JailbreakEval | Apache-2.0 | Active, ~120★ | CLI unifying ~90 jailbreak evaluators (GCG, Llama-Guard, persuasion, refusal classifiers). | Subprocess to score whether attacks succeeded. |
| **jailbreak-evaluation** (controllability) — github.com/controllability/jailbreak-evaluation | Apache-2.0 | Sporadic, ~70★ | Multifaceted scoring on Safeguard Violation + Relative Truthfulness. | Lightweight library import for binary judging. |
| **llm-attacks / GCG** (Zou et al.) — github.com/llm-attacks/llm-attacks | MIT | Original dormant; nanogcg active | Reference GCG impl for universal adversarial suffixes. | Use nanogcg or BrokenHill for production. |
| **BrokenHill** (Bishop Fox) — github.com/BishopFox/BrokenHill | MIT | Active, ~110★ | Productionized GCG runnable on RTX 4090; multi-quantization transfer. | Subprocess for white-box adversarial suffix generation. |
| **AmpleGCG** (OSU-NLP) — github.com/OSU-NLP-Group/AmpleGCG | **OpenRAIL-S/M/D (restrictive)** | Sporadic, ~110★ | Trained generator emitting GCG suffixes in minutes. | Reference architecture only. |
| **HouYi** (USENIX Sec'24) — github.com/LLMSecurity/HouYi | MIT | Sporadic, ~280★ | Black-box auto-PI: 3-component payload (Framework/Separator/Disruptor) × 3-phase loop. Found injections in Notion + 30 other apps. | **Direct architectural lift** — exact pattern for autonomous pentest agent. |
| **BIPIA** (Microsoft, KDD'25) — github.com/microsoft/BIPIA | MIT | Stable, ~250★ | Indirect-PI benchmark across 5 tasks, 250 attacker goals. | Lift indirect-injection dataset for embedding in tool outputs. |
| **SecAlign / Meta-SecAlign** (Meta) — github.com/facebookresearch/SecAlign | **CC-BY-NC** | Active | DPO defense; tests against naive/ignore/completion/gcg/advp. | Reference defended-target landscape. |
| **Agentic Radar** (SplxAI) — github.com/splx-ai/agentic-radar | Apache-2.0 | Very active, ~920★, v0.14 | Static + dynamic scanner for LangGraph/CrewAI/n8n/OpenAI Agents/AutoGen/MCP; OWASP/MAESTRO mapping; YAML adversarial test mode. | **Top-priority** — fits MCP scope exactly; lift mapping table. |
| **AgentFence** — github.com/agentfence/agentfence | MIT | Sporadic, ~70★ | Predefined probes (PI, role confusion, secret leakage, system-instruction exposure). | Lift probe-class structure. |
| **agentic_security** (msoedov) — github.com/msoedov/agentic_security | Apache-2.0 | Active, ~1.7k★ | Multimodal attacks, multi-step jailbreaks, fuzzing, RL-adaptive attacks; ships an MCP server. | Run as standalone or library import. |
| **Inspect AI** (UK AISI) — github.com/UKGovernmentBEIS/inspect_ai | MIT | Very active, ~3.3k★ | Task/Solver/Scorer + ReAct agent + sandboxed exec + Agent Bridge to OpenAI/LangChain/Pydantic-AI. | **Top-tier base framework**; install AgentDojo + Cybench evals. |
| **LLAMATOR** — github.com/LLAMATOR-Core/llamator | **CC-BY-NC-SA** | Active, ~280★ | Attack/tested/judge model triumvirate; OWASP/MITRE presets; multistage_depth. | **NC license** — reference attack catalog only. |
| **Spikee** (WithSecure/Reversec) — github.com/WithSecureLabs/spikee | MIT | Active, ~700★ | "Simple PI Kit"; document × jailbreak × instruction generator; Burp Intruder export. | **High leverage** — generation pattern + custom-target hooks. |
| **AgentShield** (affaan-m) — github.com/affaan-m/agentshield | MIT | Active 2026 | Scans `.claude/` configs + MCP + tool perms; multi-agent red/blue/auditor. | Lift `.claude/` config attack architecture. |
| **last_layer** (dmarx) — github.com/dmarx/last_layer | MIT | Sporadic | Low-latency PI pre-filter. | Defense-side reference. |
| **LangKit** (WhyLabs) — github.com/whylabs/langkit | Apache-2.0 | Sporadic (company wound down; OSS lives) | Telemetry/guardrail functions: jailbreak, PI, PII, hallucination signals. | Detection pattern reference. |
| **PISmith** — github.com/albert-y1n/PISmith | MIT | New 2025 | RL-trained attacker against named defenses (SecAlign/PromptGuard/PromptArmor/Sandwich/DataSentinel/PIGuard). | Lift attacker-RL loop. |

## 2. MCP-specific security scanners

| Name | License | Status | What it does | How to use |
|---|---|---|---|---|
| **Snyk Agent Scan / Invariant mcp-scan** — github.com/invariantlabs-ai/mcp-scan, github.com/snyk/agent-scan | Apache-2.0 (OSS) + Snyk SaaS | Very active, ~1.1k–1.5k★ | Static + dynamic + proxy scanner across Claude/Cursor/Windsurf/Gemini/Amp/Q configs; tool poisoning, shadowing, rug-pulls, toxic flows, credentials. | **Primary reference**; lift YARA + LLM-judge sets, proxy-mode runtime monitoring. Wrap as subprocess. |
| **Cisco mcp-scanner** — github.com/cisco-ai-defense/mcp-scanner | Apache-2.0 (OSS); Cisco AI Defense API commercial | Active, enterprise | Multi-engine (API + YARA + LLM-judge + behavioral); Python/TS/Go/Java/Rust/Ruby/PHP source. | **Best multi-engine architecture reference**; lift analyzer-plugin model. |
| **MCP-Shield** (riseandignite) — github.com/riseandignite/mcp-shield | MIT | Sporadic | `npx mcp-shield` for IDE configs; hidden instructions, shadowing, exfil, ~/.ssh access; bait-and-switch via `--identify-as`. | Lift hidden-instruction regex catalog; bait-and-switch test. |
| **mcpscan.ai** | Proprietary SaaS | Active | Hosted scanner with web UI; tool poisoning, command injection, confused deputy. | Reference for hosted-scanning UX + risk-scoring schema. |
| **FuzzingLabs MCP Security Hub** — github.com/FuzzingLabs/mcp-security-hub | Mixed (per-tool) | Active | **Not a scanner** — 38 Dockerized MCP servers exposing 300+ offensive tools (Nmap, Nuclei, Ghidra, SQLMap, Burp, ZAP, capa, YARA). | Wire in as the agent's offensive toolbelt. |
| **hexstrike-ai** (0x4m4) — github.com/0x4m4/hexstrike-ai | MIT | Very active | MCP server bridging 150+ pentest tools + 12+ autonomous AI agents (FastMCP-based). | **Closest existing analog**; lift multi-agent orchestration; treat as both reference AND target. |
| **DMontgomery40/mcp-security-scanner** | MIT | Sporadic | Plugin-based JS vuln scanner. | Reference for JS source static-analysis. |
| **Lasso MCP Gateway** — github.com/lasso-security/mcp-gateway | MIT (gateway); paid plugins | Active | Plugin proxy + reputation scanner (Smithery + NPM + GitHub data); PII via Presidio. | Reference proxy/guardrail architecture; lift reputation-scoring. |
| **Trail of Bits mcp-context-protector** — github.com/trailofbits/mcp-context-protector | Apache-2.0 | Active, ~208★ | TOFU pinning + LlamaFirewall guardrails; defends "line jumping" PI, ANSI terminal-code, history exfil. | Reference for ETDI-style pinning; bypass as test case. |
| **Backslash Security MCP** — backslash.security | Proprietary | Commercial, active | Discovery + vetting + hardening + real-time MCP Proxy; SIEM integration. | Competitor reference; enterprise feature checklist. |
| **mcp-watch** (kapilduraphe) — github.com/kapilduraphe/mcp-watch | OSS | Sporadic | TS source-static scanner; modular per-vuln scanner classes (Credential/ParameterInjection/etc.). | **Excellent modular reference**; lift per-vuln class architecture. |
| **Ramparts** (getjavelin) — github.com/getjavelin/ramparts | OSS | Active | Fast Rust MCP scanner; HTTP/SSE/stdio/subprocess; YARA + cross-origin + LLM analysis. | Strong reference for transport-fallback handling. |
| **Agent Shield** (elliotllliu) — github.com/elliotllliu/agent-shield | MIT-style | Active | 13 engines, 31 rules, 8-language PI patterns; cross-file taint; MCP runtime proxy. | Lift cross-file taint tracking + 31-rule catalog. |
| **qsag-core** (Neoxyber) — github.com/Neoxyber/qsag-core | MIT | Active | Tool-poisoning + agent security toolkit aligned to OWASP Agentic Top 10 2026; 13 named pattern categories. | **Highest-value pattern catalog to lift directly**. |
| **Golf-Scanner** — github.com/golf-mcp/golf-scanner | OSS | Active | Cross-IDE config discovery (Claude Code/Cursor/VSCode/Windsurf/Gemini/Kiro/Antigravity); 20 checks; 0–100 risk score. | Lift risk-scoring formula. |
| **mcpx** (kwonye) — github.com/kwonye/mcpx | OSS | Active | **Not a scanner** — gateway/manager syncing managed MCPs to multiple clients with secret-store auth. | Use for the agent's own MCP-client harness. |

## 3. Agent security and benchmarks

| Name | License | Status | What it does | How to use |
|---|---|---|---|---|
| **AgentDojo** (ETH Zurich) — github.com/ethz-spylab/agentdojo | **AGPL-3.0** | Active, ~700★ | NeurIPS'24 D&B; 97 user tasks, 629 security tests, 70 tools across Workspace/Slack/Travel/Banking. AISI-adopted. | **Primary PI benchmark**; lift Important-Instructions + tool-knowledge attacks. AGPL caution. |
| **AgentHarm** (Anthropic / Gray Swan) — in inspect_evals | MIT | Active | 110 harmful agent tasks (440 augmented) across 11 harm categories. | Benchmark refusal robustness. |
| **InjecAgent** (UIUC) — github.com/uiuc-kang-lab/InjecAgent | MIT | Stable, ~200★ | 1,054 IPI tests; 17 user tools, 62 attacker tools; direct-harm + data-exfil. | Lift attack catalog; benchmark tool-using agents. |
| **ASB / Agent Security Bench** — github.com/agiresearch/ASB | MIT | Active, ~150★ | 10 scenarios, 27 attack/defense methods, 7 metrics; PoT backdoor + memory poisoning. | Lift attack taxonomy. |
| **AgentBench** (Tsinghua) — github.com/THUDM/AgentBench | Apache-2.0 | Very active, ~3.2k★ | 8 environments (OS shell, DB SQL, KG, ALFWorld, WebShop, Mind2Web). | Tool-using competence baseline. |
| **ToolEmu** (UofT) — github.com/ryoungj/ToolEmu | MIT | Stable, ~600★ | LM-emulated tools: 36 toolkits, 311 tools, 144 cases. | Architecture template for emulating risky tools. |
| **WebArena / VisualWebArena** — github.com/web-arena-x | Apache-2.0 | Active | 812 web tasks across 6 self-hosted realistic envs. | Self-host as adversarial target environment. |
| **WASP** (Meta FAIR) — github.com/facebookresearch/wasp | CC-BY-NC + MIT | Recent | Web-agent PI benchmark on (V)WebArena; targets GPT-4o + Claude Computer Use. | Direct browser-agent attack target. |
| **τ-bench / τ²-bench / τ³-bench** (Sierra) — github.com/sierra-research/tau-bench | MIT (code), CC-BY-NC (data) | Very active, ~1k★ | Tool-Agent-User with simulated users; airline/retail/telecom/banking. | Multi-turn reliability + policy adherence. |
| **GAIA** — gaia-benchmark on HF | Apache-2.0 | Active leaderboard | 466 questions for general assistants needing reasoning + tool use + multimodality + browsing. | Capability baseline. |
| **AgentSafetyBench** (THU-CoAI) — github.com/thu-coai/Agent-SafetyBench | Apache-2.0 | Released 2025 | 349 envs, 2k cases, 8 risk categories; none of 16 agents scored >60%. | Lift failure-mode taxonomy. |
| **R-Judge** — paper arXiv:2401.10019 | Open | Stable | 569 multi-turn agent records; 27 risk scenarios. | Build safety-judge component. |
| **SafeAgentBench** — github.com/shengyin1224/SafeAgentBench | MIT | Active | Embodied-agent safety, AI2-THOR, 750 tasks. | Niche embodied scope. |
| **AgentBoard** (HKUST) — github.com/hkust-nlp/AgentBoard | MIT | Active, ~700★ | NeurIPS'24 Oral; 9 tasks, 1013 envs; progress-rate metric. | Capability-baseline diagnosis. |
| **AgentDyn** — github.com/SaFo-Lab/AgentDyn | MIT | Recent | Open-ended dynamic AgentDojo extension; CaMeL/Progent/DRIFT/PIGuard/PromptGuard2 defenses. | Supplement AgentDojo. |
| **OS-Harm / AgentHazard** — arXiv | Open | Recent | Computer-use-agent safety on OSWorld; 73.63% ASR on Claude Code w/ Qwen3-Coder. | Computer-use agent benchmarks. |

## 4. Autonomous offensive AI agents

| Name | License | Status | What it does | How to use |
|---|---|---|---|---|
| **PentestGPT** (GreyDGL) — github.com/GreyDGL/PentestGPT | MIT | Very active, ~11k★ | Reasoning/Generation/Parsing modules + task-tree; v1.0 hits 86.5% on 104-task XBOW at $1.11 avg/run. | Lift modular Reason/Gen/Parse architecture. |
| **HexStrike AI** (0x4m4) — github.com/0x4m4/hexstrike-ai | MIT | Very active | Bridges 150+ tools to AI; 12+ specialist agents (TechDetector, BugBountyManager, CVEIntel, ExploitGen, VulnCorrelator, ParamOptimizer, CTFManager). | **Direct competitive landscape**; lift orchestration; use as MCP target. |
| **hackingBuddyGPT** (TU Wien) — github.com/ipa-lab/hackingBuddyGPT | MIT | Active (GH Accelerator) | 50-LoC framework; Linux PrivEsc / web pentest / API testing; Vagrant+Ansible test-bed. | Lift 50-line agent + Capability composition pattern. |
| **Cybersecurity AI / CAI** (Alias Robotics) — github.com/aliasrobotics/cai | Dual: MIT (openai-agents parts) + non-commercial research-only core | Very active, ~3k★ | 300+ models; HTB Top-30 Spain in a week; CAIBench meta-benchmark. | Architecture reference (Red/Bug-Bounty/Blue patterns); CAIBench is meta-eval. **License caution**. |
| **Nebula** (Beryllium Security) — github.com/berylliumsec/nebula | BSD-2 (community) | Active | Terminal-embedded NL pentest; Pro adds autonomous mode + DAP. | Reference for NL-CLI pentest. |
| **Vulnhuntr** (Protect AI) — github.com/protectai/vulnhuntr | **AGPL-3.0** | Active 2025, ~2.6k★ | Zero-shot vuln discovery: LLM + Jedi static analysis traces user-input → server-output across files; found 12+ 0-days. | Lift call-chain reasoning. **AGPL forces open-source if integrated**. |
| **BurpGPT** (aress31) — github.com/aress31/burpgpt | Apache-2.0 (community); Pro commercial | Active | Burp extension running GPT/Claude/Gemini on intercepted traffic. | Reference for HTTP-traffic LLM analysis pipeline. |
| **PenTestAgent** (WiSec'25) — github.com/nbshenxm/pentest-agent | MIT (likely) | Recent | 3-agent: Recon + Planning (CVE prio) + Execution; on Vulhub Docker CVEs. | Lift Recon→Plan→Execute pattern + CVE scoring. |
| **AutoAttacker** (Xu et al. 2024) — arXiv:2403.01038 | Paper | 2024 | Multi-sub-agent post-breach (Metasploit + RAG); GPT-4 substantially > GPT-3.5. | Lift post-breach attack catalog. |
| **AutoPentester / Pentest-Swarm-AI** (Armur-Ai) — github.com/Armur-Ai/Auto-Pentest-GPT-AI | MIT | Active 2025 | Go-based multi-agent (Recon/Class/Exploit/Report); Claude API + 7 native tools; +27% vs PentestGPT on HTB. | Compare to your design; lift swarm pattern. |
| **PentAGI** (vxcontrol) — github.com/vxcontrol/pentagi | Open | Active | Fully autonomous, 11+ specialist agents; supervision essential for <32B models. | Reference for agent supervision/limit enforcement. |
| **White Rabbit Neo** — kindo.ai (model, not agent) | Open + Kindo policy | Active | Uncensored offensive-security fine-tune. | Candidate model backbone. |
| **IRIS** (Penn/Cornell) — arXiv:2405.17238 | Open | Updated 2025 | Neuro-symbolic LLM + CodeQL; CWE-Bench-Java (120 Java CVEs). | Lift static-analysis-augmented LLM vuln finding. |
| **Cybench** (Stanford CRFM) — github.com/andyzorigin/cybench | MIT | Very active | 40 professional CTF tasks (HTB, SekaiCTF, Glacier, HKCert); subtask-guided + unguided. **De-facto frontier offensive benchmark.** | Mandatory comparison. |
| **BountyBench** (Stanford) — bountybench.github.io | MIT | Active 2025 | 25 systems, 40 bounties ($10–$30,485), 9/10 OWASP Top 10; Detect/Exploit/Patch = 120 tasks. | Premier real-world dollar-impact benchmark. |
| **NYU CTF Bench + D-CIPHER** — github.com/NYU-LLM-CTF | MIT | Very active | 200+55 dockerized CSAW CTF challenges; Planner+Executor+Auto-prompter agents. | Direct benchmark + agent reference architectures. |
| **CVE-Bench** (UIUC) — github.com/uiuc-kang-lab/cve-bench | MIT | Active 2025, ICML | Real-world critical-CVE web app benchmark; SOTA ~13% exploit success. | Real-world web-CVE benchmark. |
| **RedAgent** — github.com/QuirkShark/RedAgent | Open | Active | Multi-agent jailbreak; 5-query black-box jailbreak; found 60 vulns in custom GPTs. | Lift jailbreak-strategy abstraction + skill-memory. |
| **CIPHER** (Sensors 2024) — github.com/ibndias/CIPHER | Apache-2.0 | 2024 | Open-weights LLM fine-tuned on 300+ HTB write-ups; FARR Flow methodology. | Candidate fine-tune; FARR eval methodology. |
| **EnIGMA / SWE-agent** — github.com/SWE-agent/SWE-agent | MIT | Very active, ~18.5k★ | Pivoted to offensive CTF mode (NYU CTF 3.3× SOTA); ACI + Summarizer. | Lift Agent-Computer Interface pattern. |
| **CyberSecEval 1–4** (Meta) — github.com/meta-llama/PurpleLlama | MIT | Very active | CSE-3: autonomous offensive cyber-ops; CSE-4: AutoPatchBench + CyberSOCEval. | Closest analog to evaluating your agent. |
| **HAL Harness** (Princeton/CRFM) — github.com/steverab/hal-harness | MIT | Active | Unified eval harness for SWE-bench-Verified, USACO, AppWorld, AgentHarm, GAIA, Cybench, tau-bench. | **Use as your harness**. |
| **ProjectDiscovery Neo** — projectdiscovery.io/ai | Commercial | Active | Closed-source AI-powered scanner extending Nuclei. | Competitive landscape only. |

## 5. Prompt-injection corpora and academic safety datasets

| Name | License | What it provides |
|---|---|---|
| **AdvBench** (Zou et al.) — github.com/llm-attacks/llm-attacks | MIT | 500 harmful behaviors + 500 strings; canonical GCG baseline. |
| **HarmBench** (CAIS) — github.com/centerforaisafety/HarmBench | MIT | ~510 behaviors across Standard/Contextual/Copyright/Multimodal + Llama-2/Mistral judges. |
| **JailbreakBench** — github.com/JailbreakBench/jailbreakbench | MIT | 100 harmful + 100 benign across 10 OpenAI categories; live artifact leaderboard. |
| **HackAPrompt dataset** — HF: hackaprompt/hackaprompt-dataset | MIT | 600K real adversarial prompts from global competition; 29-class ontology. |
| **StrongREJECT** — github.com/dsbowen/strong_reject | MIT | 313 forbidden prompts across 6 categories + fine-tuned Gemma-2B judge (SOTA). |
| **MaliciousInstruct** — github.com/Princeton-SysML/Jailbreak_LLM | Unspecified | 100 instructions across 10 intents. |
| **LatentJailbreak** — github.com/qiuhuachuan/latent-jailbreak | MIT | 416 prompts with embedded malicious instruction in benign meta-task. |
| **Do-Not-Answer** — github.com/Libr-AI/do-not-answer | **CC-BY-NC-SA** | 939 should-refuse instructions; 3-level taxonomy. |
| **XSTest** — github.com/paul-rottger/xstest | CC-BY 4.0 | 250 SAFE + 200 UNSAFE prompts; over-refusal calibration. |
| **HH-RLHF** (Anthropic) — HF: Anthropic/hh-rlhf | MIT | 170K preference pairs + 38K red-team transcripts. |
| **BeaverTails** (PKU) — HF: PKU-Alignment/BeaverTails | **CC-BY-NC** | 333,963 QA pairs, 14 harm categories + 361,903 preferences. |
| **PKU-SafeRLHF** | CC-BY-NC | ~297K preference pairs with safety + helpfulness labels. |
| **ToxicChat** — HF: lmsys/toxic-chat | CC-BY-NC | 10K real Vicuna-demo conversations with toxicity + jailbreak labels. |
| **RealToxicityPrompts** — HF: allenai/real-toxicity-prompts | Apache-2.0 | 100K prompts with Perspective API toxicity scores. |
| **Aegis Content Safety v1/v2** — HF: nvidia/Aegis-AI-Content-Safety-Dataset-2.0 | CC-BY-4.0 | 11K → 33K human-labeled interactions; 13-cat taxonomy. |
| **PINT Benchmark** (Lakera) — github.com/lakeraai/pint-benchmark | Custom (results public; data by request) | 4,314 inputs incl. multilingual + hard negatives; held-back. |
| **deepset/prompt-injections** — HF: deepset/prompt-injections | Apache-2.0 | 662 EN+DE prompts; trained deberta-v3-base. |
| **jayavibhav/prompt-injection** — HF | Unspecified | 327K rows binary-labeled. |
| **BIPIA** (Microsoft) — github.com/microsoft/BIPIA | MIT (code), CC-BY-SA (data) | Indirect-PI across Email/Web/Table QA + Summarize + Code QA. |
| **TrustLLM** — github.com/HowieHwong/TrustLLM | MIT | 8 trustworthiness dimensions, 31 tasks across >30 datasets. |
| **SafetyBench** (THU-CoAI) — github.com/thu-coai/SafetyBench | MIT | 11,435 MCQs across 7 safety categories. |
| **ALERT** (Babelscape) — github.com/Babelscape/ALERT | **CC-BY-NC-SA** | 45K + 9.45K adversarial prompts; 32-micro-cat taxonomy aligned to EU AI Act. |
| **WMDP** (CAIS) — github.com/centerforaisafety/wmdp | MIT | 4,157 expert MCQs covering bio/cyber/chem dual-use knowledge. |
| **AART** (Google) | Apache-2.0 | ~3,269 demo prompts via AI-assisted recipe. |
| **WildJailbreak** (AI2) — HF: allenai/wildjailbreak | ODC-BY + AI2 RUG (gated) | 262K synthetic safety pairs across 13 risk categories. |
| **WildGuardMix** (AI2) — HF: allenai/wildguardmix | ODC-BY + RUG (gated) | Multi-task moderation + WildGuard 7B moderator (~GPT-4 quality). |
| **SafetyPrompts.com** (Röttger) | Index | Living catalogue of ~100 open safety datasets w/ metadata. |

**Awesome-list discovery indexes:** corca-ai/awesome-llm-security · chawins/llm-sp · yueliu1999/Awesome-Jailbreak-on-LLMs · Libr-AI/OpenRedTeaming · user1342/Awesome-LLM-Red-Teaming · Meirtz/Awesome-LLM-Jailbreak.

**General payload libraries:** swisskyrepo/PayloadsAllTheThings (now has Prompt Injection section, MIT) · danielmiessler/SecLists (MIT) · fuzzdb-project/fuzzdb (BSD) · OWASP cheat sheets · Giskard-AI/prompt-injections.

## 6. x402 ecosystem

**Core spec + reference SDKs:**
- **coinbase/x402** (Apache-2.0, ~5.5k★) — TS/Go/Python/Rust SDKs (`@x402/core/evm/svm/axios/fetch/express/hono/next/paywall`). v2 (Dec 2025): CAIP-2 IDs, sessions, dynamic payTo. **Foundational dependency.**
- **x402-rs** (OSS) — production Rust facilitator + `x402-axum` + `x402-reqwest`; self-hostable.
- **x402 Kit (Rust)**, **x402-go** (community), **michielpost/x402-dotnet**, **QuickNode x402-rails / x402-payments** (Ruby), **Mogami Java SDK** (Spring Boot).
- **BofAI/x402** — Multi-chain TS+Python SDK with TIP-712 + EIP-712, TRON GasFree, BSC.

**Discovery / scanners:**
- **Merit-Systems/awesome-x402** (CC0, 110★) and **xpaysh/awesome-x402** — canonical lists.
- **x402scan** (Merit) — x402scan.com — **THE ecosystem explorer**, transaction indexer, submit-a-URL endpoint at `/resources/register`. **Primary target discovery for the agent.**
- **x402station**, **x402list.fun**, **Rencom**, **EntRoute**, **Bazaar** (Coinbase built-in marketplace).
- **x402-watch** (community) — full lifecycle verification (402→sign→200) on Base Sepolia. **Direct reference architecture for a probe agent.**
- **x402lint** — CLI/SDK validator for payment configs.
- **x402 Playground** (QuickNode) — interactive testing.

**Facilitators:**
- **Coinbase CDP** (default; OFAC/KYT; free 1k tx/mo, then $0.001/tx).
- **x402.org Facilitator** (testnet default — Base Sepolia, Solana Devnet, Stellar testnet, Aptos testnet).
- **thirdweb** (170+ chains, 4000+ tokens), **PayAI**, **Corbits Faremeter**, **Nevermined** ("programmable x402" with ERC-4337/sessions/credit billing; SOC-2/ISO/PCI), **Stripe x402** (Feb 2026 USDC), **Cloudflare Workers/Agents SDK** (`paidTool`/`withX402`), **AWS** (CloudFront+WAF sample), **Vercel x402-mcp**, **Stellar facilitator** (OZ Relayer, audited smart accounts), **OpenZeppelin Relayer plugin**.
- Listed on x402.org: 0xArchive, 0xmeta, AutoIncentive, Bitrefill, Dexter, Elsa, fretchen.eu, GoPlausible (Algorand), Heurist (OFAC), Hydra Protocol, KAMIYO, Kobaru, OpenFacilitator, OpenX402.ai, Polygon, Primer, RelAI, SolPay, Treasure, Ultravioleta DAO (19 mainnets, ERC-8004 reputation), WorldFun, xEcho, **xpay Facilitator** (xpay.sh), Meridian, Faremeter, Onchain, **0x402.ai** (cloud-platform-to-become-a-facilitator).

**Server middleware / gateways:**
- **Faremeter** (OSS framework — high-quality reference) — github.com/faremeter/faremeter.
- **tollbooth** — single-YAML gateway with dynamic pricing, multi-upstream, SSE, hooks. **Best-fit for a target sandbox to attack.**
- **Atomic Rail**, **Foldset**, **Proxy402** (Fewsats), **solana-pay-x402**, **Pipegate**, **Run402**, **Spraay**, **Daydreams Router** (LLM inference router).
- **AltLayer x402 Suite** (gateway + facilitator + Autonome agent hosting).
- **PEAC Protocol** — cryptographic receipts; **x402r** — non-custodial refund/arbitration; **px402** (PRXVT) — ZK shielded; **FluxA** — deferred parallel micropayments + batch settlement.

**Wallets / agent kits / paying clients:**
- **Crossmint x402 + Agent Wallets** — multi-protocol (x402/AP2/ACP), 15+ chains, USDC/USDT/PYUSD; VASP, SOC-2.
- **Latinum**, **Locus**, **ClawPay MCP**, **ampersend**, **Primer Pay**, **Meson x402** (Chrome ext), **1Pay.ing**, **AgentCash**, **AgentMail**, **OpenPayment**, **Conway Automaton**, **Bino**.
- **x402-proxy** (npx) — CLI auto-payer + MCP stdio proxy. **Highly relevant for the pentest agent.**
- **x402-pay**, **ag402** (Solana USDC, ~0.5s, 648+ tests, non-custodial).
- **MCPay** — github.com/microchipgnu/MCPay — OSS infra for MCP x402 payments. **MCPay Build** (no-code MCP server builder + monetization).
- **PayMCP** (npm: paymcp) — MCP payment layer; native Mode.X402.
- **x402-mcp** (Vercel) — `paidTool` wrapper.
- **mark3labs/mcp-go-x402**, **fernsugi/x402-api-mcp-server**, **Oops!402** (ChatGPT/Claude remote MCP), **Coinbase MCP example**.

**Spend controls / policy / observability:**
- **PolicyLayer** — policylayer.com — non-custodial spend limits, two-gate enforcement, signed decisions, MCP **Intercept** proxy. MIT, 1.4.0. **Strong reference; mandatory for the pentest agent.**
- **PaySentry** (mkmkkkkk/paysentry) — control plane with **MockX402/MockACP/MockAP2** sandbox. **Excellent test harness.**
- **x402-secure** (T54), **ActionGate**, **BlackSwan**, **Augur** ($0.10/call admission control).
- **zauth** — continuous endpoint verification + RepoScan + auto-refunds. **Direct competitor.**
- **ShieldAPI MCP** — 9-tool security MCP (breach, domain rep, URL safety, PI detection, skill scanning) priced via x402. **Direct overlap with your mission.**
- **AI Security Guard** — five-analyzer firewall priced via x402.
- **Orac** — agent trust scoring (265-entity KG with PageRank).
- **MerchantGuard** — GuardScore/GuardScan/**Mystery Shopper** (10-probe agent certification). **Closest existing analog to your product.**
- **Cybercentry**, **QuantumShield**, **Rug Munch Intelligence** (19 endpoints), **Kevros** (ML-DSA-87 PQ sigs), **OMATrust** (decentralized reputation via EAS), **Slinky Layer** (ERC-8004), **DJD Agent Score**, **Trusta.AI**, **Idapixl Cortex**, **Mycelia Signal**.

**xpay.sh suite:** xpay Facilitator + Smart Proxy + Paywall-as-a-Service + Transaction Explorer + `@xpaysh/agent-kit-core/langchain/testing` (mock x402 server). **Most directly relevant existing kit** for paying-agent builds.

**Adjacent payment protocols:** L402 (Lightning Labs predecessor) · AP2 (Google, x402 wraps as crypto rail) · ACP (OpenAI+Stripe) · MPP (Stripe Tempo, Mar 2026) · Skyfire KYAPay · Payman AI · Halliday · Lit Protocol "Chipotle" v3.

## 7. Traditional security tooling (subprocess-invokable)

| Tool | License | Use |
|---|---|---|
| **nuclei** + **nuclei-templates** | MIT | YAML-DSL vuln scanner; `subprocess.run([\"nuclei\", \"-target\", url, \"-jsonl\"])`. ~28k★. |
| **httpx**, **naabu**, **subfinder**, **katana**, **dnsx** | MIT | ProjectDiscovery recon DAG; uniformly JSON output. |
| **gau** / **waybackurls** | MIT | Historical URL discovery. |
| **ffuf** | MIT | Fast Go web fuzzer; ~14k★. |
| **sqlmap** | GPLv2 | Automated SQLi. |
| **nikto** | GPL | Web server / CGI scanner. |
| **wpscan** | WPScan PSL | WordPress scanner; vuln-DB API token required. |
| **gobuster**, **dirsearch**, **arjun** | Apache-2.0 / GPL | URI/DNS/vhost/param brute-force. |
| **OWASP ZAP** | Apache-2.0 | Full DAST proxy + REST API + Automation YAML; Docker. |
| **semgrep** | LGPL-2.1 | AST-aware static analysis. |
| **bandit** | Apache-2.0 | Python AST security linter. |
| **CodeQL** | Source-available; **OSS-only free** | Deep dataflow/taint via QL. |
| **trivy** | Apache-2.0 | Container/FS/git CVE + IaC + secrets + SBOM; ~31.7k★. |
| **grype** + **syft** | Apache-2.0 | CVE scanner + SBOM generator. |
| **gitleaks** | MIT | Fast regex secret scanner. |
| **trufflehog** | **AGPL-3.0** | 800+ verified-secret detectors. |
| **OWASP amass** | Apache-2.0 | OSINT/DNS asset mapper; ~14.2k★. |
| **prowler** | Apache-2.0 | Multi-cloud (AWS/Azure/GCP/K8s/M365) security audit; 572+ AWS checks, 41 frameworks. |
| **Scout Suite** | GPLv2 | Multi-cloud audit — **stale (May 2024)**; prefer prowler. |

## 8. Smart contract / EVM tooling

**Dev frameworks:** Foundry (Apache/MIT) · Hardhat (MIT).
**Clients:** viem (MIT, modern TS) · ethers.js v6 (MIT, EAS SDK requires) · ethers-rs (deprecated → alloy) · alloy (Apache/MIT, Paradigm Rust v1.0) · web3.py (MIT, **likely your primary**) · web3.js (LGPL).
**Contracts:** OpenZeppelin Contracts (MIT) — bounty pool, registries, Safe modules.
**Attestations:** EAS contracts + EAS SDK (MIT) — live on Base Sepolia (base-sepolia.easscan.org) · **Sign Protocol** (omni-chain alternative).
**Sigstore reference:** cosign + Rekor (Apache-2.0) — append-only Merkle log pattern.
**Wallets:** Privy (Stripe-acquired, TEE-backed sharded keys, server-side wallets, policy engine) · Dynamic (TSS-MPC, Fireblocks-acquired) · Magic · thirdweb SDK (Apache-2.0, x402 v2 support).
**Base Sepolia:** Base RPC docs (chain 84532) · Coinbase Cloud Node.
**Account abstraction:** ERC-4337 spec · Pimlico (Alto bundler Apache-2.0; **permissionless.js** on viem) · Alchemy Account Kit (`@alchemy/aa-core` MIT).
**Multisig:** Safe (LGPL-3 contracts; MIT SDK; **Safe Modules for autonomous bounded payouts**).
**Registry patterns:** ERC-7572 contractURI · ENS resolver registries (BSD-2).

## 9. Onchain bug bounty and disclosure

- **Immunefi** — REST API; community CLI **ibb** (github.com/infosec-us-team/ibb) wraps it like jq. >$190B user funds covered; programmatic scope-check.
- **HackerOne** — REST API at api.hackerone.com.
- **Sherlock** — audit contests + protocol exploit insurance ($500k post-launch).
- **Code4rena** (acquired by Zellic) · **Cantina+Spearbit** (unified 2025) · **CodeHawks** (Cyfrin).
- **Hats Finance** — onchain decentralized bounties with hash-only submissions; reference contract `HackFirstBountyLater` is a minimal escrow ideal for your bounty pool.
- **Hats Protocol** — ERC-1155 onchain roles; pair with Safe Modules + EAS attestations.
- **OpenBounty** (Status, archived) — historical reference.
- **Disclosure norms:** RFC 9116 security.txt · disclose.io templates · CERT/CC + OWASP RD policy templates.
- **ZK proof of vuln:** TLSNotary + Sign Protocol's zkAttestations as a forward path; stub `zkProofURI` field in your EAS schema.

## 10. ENS-based identity and agent identity

- **ens-contracts** (BSD-2) · **ENSjs v4** (MIT, viem-based) · **ENSNode** (NameHash; multichain ENS indexer 10× faster than Subgraph; indexes Basenames, Lineanames, 3DNS, NameStone/NameSpace/Justaname) · **ENSRainbow** (heals labelhashes).
- **SIWE / ERC-4361** — `siwe` library (Apache/MIT, SpruceID) · siwe.xyz validator/OIDC.
- **Subnames stack:** **Durin** (NameStone Foundry contracts, MIT — L1 + L2Registry CCIP-Read pattern) · **NameStone** (gasless API, Indexed) · **Justaname** · **NameSpace** · **CCIP-Read EIP-3668**.
- **Basenames** (Coinbase) — github.com/base/basenames (MIT) — **strongly recommended** as primary `<agent>.base.eth` identity; uses EAS attestations on Base for discount eligibility.
- **ERC-8004 — Trustless Agents** — three registries (Identity ERC-721 with URIStorage; Reputation `giveFeedback`/`readAllFeedback`; Validation w/ TEE hooks). Mainnet launch Jan 29, 2026 across 20+ networks. Sepolia: IdentityRegistry `0x8004A818BFB912233c491871b3d84c89A494BD9e`. **Canonical Agent ID Trust Registry — pair with Basenames.**
- **Phala Network ERC-8004 TEE Agent** (Apache) — reference impl with Intel TDX.
- **Coinbase Agent ID stack:** ENS/Basenames + ERC-8004 + x402 + World AgentKit (delegation for humanity proof).
- **W3C DID v1.1** (Candidate Rec March 2026) · **ethr-did** (uport-project, MIT). **WebID for agents** is conceptual only — ERC-8004 + DID is the practical path.
- **IETF GNAP (RFC 9635)** — forward-looking auth protocol for agent delegation.

## 11. Payload libraries and OWASP standards

- **swisskyrepo/PayloadsAllTheThings** (MIT) — now has Prompt Injection section.
- **danielmiessler/SecLists** (MIT) — fuzzing wordlists.
- **fuzzdb-project/fuzzdb** (BSD).
- **Giskard-AI/prompt-injections** — small curated PI payloads.
- **OWASP LLM Top 10** (2025) — CC-BY-SA; map every finding to LLM01–LLM10.
- **OWASP Top 10 for Agentic Applications 2026** (Dec 10, 2025) — ASI01–ASI10 (Goal Hijack, Identity/Privilege Abuse, Tool Misuse, Delegated Trust, Memory Poisoning, Cascading Failures, Supply Chain incl. MCP, Resource Exhaustion, Unsafe Tool/Code Execution, Rogue Agents). **Primary taxonomy for agent findings.**
- **OWASP Agentic Skills Top 10 (AST10)** — covers vibe-coded skill layer (CVE-2025-59536, CVE-2026-21852 in Claude Code, ClawJacked CVE-2026-28363).
- **OWASP API Security Top 10 (2023)** — BOLA/BOPLA/BFLA/SSRF for non-AI surfaces.
- **OWASP ASVS v5.0** — verification baseline.
- **OWASP Web Security Testing Guide** + Cheat Sheet Series.
- **Microsoft Agent Governance Toolkit** — maps to OWASP Agentic Top 10.

## 12. LLM-as-judge and verification frameworks

- **G-Eval** — paper Liu et al. EMNLP'23; reference impl in DeepEval.
- **DeepEval** (Apache-2.0, Confident-AI) — pytest-style; G-Eval, DAG, RAGAS, jailbreak detection.
- **Promptfoo grading** (MIT) — `llm-rubric`, `model-graded-closedqa`, `g-eval`, `factuality`, `select-best`; deterministic + model-graded; CI-friendly.
- **OpenAI evals** (MIT) — model-graded YAML; **simple-evals deprecated July 2025**.
- **lm-evaluation-harness** (EleutherAI, MIT, ~8k★) — backend for HF Open LLM Leaderboard.
- **Ragas** (Apache-2.0) — reference-free RAG metrics.
- **Inspect AI** (UK AISI, MIT) — **strongest match**: Solver/Scorer + Docker/k8s sandbox + Tool Approval HITL.
- **TruLens** (MIT) — feedback functions; OTel-native.
- **Langfuse evaluations** (MIT) — Ragas-partnered evaluators.
- **Phoenix Arize** (Elastic-License-2 — not OSI) — OpenInference/OTel; ~6k★.
- **HELM** (Apache-2.0, Stanford) — multi-metric.
- **BIG-Bench / BBH** (Apache-2.0).
- **Promptbench** (Microsoft, MIT) — adversarial-robustness benchmark.
- **Patronus AI / Lynx** — Llama-3 fine-tune for hallucination detection (open-weights; SDK proprietary).
- **MLflow LLM Evaluate** (Apache-2.0) — `mlflow.evaluate()` with judge metrics + 15-framework integration.
- **LangChain openevals** (MIT, ~1k★) — criteria + trajectory evaluators.
- **LlamaIndex Evaluators** (MIT) — Faithfulness/Relevancy/Correctness/Pairwise/Guideline.
- **UpTrain** (Apache-2.0) — has direct `JailbreakDetection` check.
- **Athina AI evals** (Apache-2.0).
- **GPTScore** (MIT) — historical, subsumed by G-Eval.
- **AlpacaEval** / **MT-Bench** (Apache-2.0) — capability/methodology references.
- **Arena-Hard / Arena-Hard-Auto** (Apache-2.0) — better separability than MT-Bench.

## 13. Sandboxing and isolation

| Tool | Isolation | License | Use |
|---|---|---|---|
| **Docker / runc** | OS namespaces+seccomp; **shared kernel** | Apache-2.0 | Outer wrap only — not for adversarial code. |
| **Firecracker** | **MicroVM via KVM** (~125ms boot, 5MB) | Apache-2.0 | Strongest practical isolation. Powers Lambda/Fargate. |
| **e2b** | Firecracker microVM SDK (~150–200ms) | Apache-2.0 | **Best plug-and-play SDK** for the agent. |
| **Daytona** | OCI/Docker (Kata/Sysbox option); <90ms; stateful snapshots | **AGPL-3.0** | Long-running stateful probes. AGPL caution. |
| **Modal Sandboxes** | gVisor + `block_network`/`cidr_allowlist` | Proprietary SaaS | Excellent for restricting probe egress to target subnet. |
| **gVisor (runsc)** | Userspace kernel intercepting syscalls | Apache-2.0 | Mid-tier; ~70–80% syscall coverage. |
| **Kata Containers** | MicroVM orchestrator (Firecracker/CH/QEMU) | Apache-2.0 | K8s production microVM-isolated probes. |
| **Ignite** (Weaveworks) | Firecracker microVM | Apache-2.0 | **Archived** post-Weaveworks shutdown 2024. |
| **Apple Containerization / `container`** | One lightweight VM per container | Apache-2.0 | macOS dev workstations; per-container kernel. |
| **Cloudflare Workers / Dynamic Workers** | V8 isolates + memory protection keys | Proprietary | JS/Wasm-only edge probes; <1ms cold start. |
| **Riza** (riza.io) | WASM sandbox (Py/JS/TS/Rb/PHP) <10ms | Proprietary SaaS | Lightweight LLM-generated probe scripts. |
| **Pyodide** | Browser/Deno WASM | MPL-2.0 | Inside-browser probes; pairs with langchain-sandbox. |
| **nsjail** | Namespaces + cgroups + seccomp-bpf (Kafel BPF) | Apache-2.0 | Tight per-process probe runner with explicit syscall allowlists. |
| **bubblewrap (`bwrap`)** | Userns + bind-mount + seccomp | LGPL-2.0 | Lightweight per-command sandbox. |
| **Wasmer / WasmEdge / Wasmtime** | WASM/WASI | MIT/Apache | Memory-safe portable probes. |
| **Isolate (ioi/isolate)** | Namespaces + cgroups | GPL-2.0 | Bullet-proof time-bounded contest-style execution. |
| **RestrictedPython** | AST-rewriting | ZPL-2.1 | **Not security sandbox vs malicious code**. |
| **Webcontainers** (StackBlitz) | Browser-only Node WASM | Proprietary | Browser-side only. |
| **Coder / Gitpod** | Container ephemeral envs | AGPL-3.0 | Per-task agent workspaces (outer layer). |
| **SWE-ReX / mini-swe-agent** | Pluggable: subprocess/Docker/Podman/Singularity/bwrap/Fargate | MIT | **Sandbox abstraction library** for AI agents. |
| **OpenHands** sandbox | Docker per session | MIT | Reference architecture; weak isolation. |
| **afshinm/zerobox** | Process-level + Codex sandbox primitives; **credential-injection proxy**, domain allowlist, snapshot/rollback | OSS | **Excellent middle-ground** — uniquely fits agent-holds-credentials-without-leaking. |
| **Northflank Sandboxes** | Kata/Firecracker/gVisor/CH choice | Proprietary | Production multi-tenant sandbox-as-a-service. |
| **kubernetes-sigs/agent-sandbox** | K8s CRD; pluggable runtime | Apache-2.0 | Cloud-native fleet deployment pattern. |

**Layered defense pattern:** Daytona/Coder ephemeral env (per-task) → E2B/Modal microVM (per-probe) → cidr_allowlist or zerobox `--secret-host` for target-scoped creds → Inspect AI scorers + Promptfoo CI gates.

## 14. Agent orchestration frameworks

| Framework | License | Stars | Note |
|---|---|---|---|
| **LangGraph** | MIT | ~13k | Graph state machine; **strong default** for persistent learning + HITL + durable execution. |
| **AutoGen / AG2** | MIT/Apache | ~40k | Conversational multi-agent; merging into Microsoft Agent Framework Q1 2026. |
| **CrewAI** | MIT | ~30k | Role-based crews + Flows. |
| **OpenAI Agents SDK** | MIT | ~19k | Handoff-based; replaced Swarm. Ephemeral context by default. |
| **Claude Agent SDK** | **Proprietary Anthropic** | n/a | Powers Claude Code; native MCP. |
| **Pydantic AI** | MIT | ~12k | Type-safe; OTel/Logfire native. **Strong build-on candidate**. |
| **Mastra** | Elastic License 2.0 (mostly) | ~14k | TS-first; "Observational Memory" (94.87% LongMemEval). **Best for web-first interface in TS.** |
| **Swarm** | MIT | ~19k | OpenAI experimental; **superseded** — reference only. |
| **Inspect AI Solver** | MIT | ~3.3k | Eval-grade scaffold; sandboxed; Agent Bridge to OpenAI/LangChain/Pydantic-AI. |
| **LlamaIndex Agents** | MIT | ~37k | RAG-heavy. |
| **Semantic Kernel** | MIT | ~24k | Converging into MS-AF. |
| **Haystack Agents** | Apache-2.0 | ~17k | Production RAG with agent loop. |
| **Smolagents** (HF) | Apache-2.0 | ~26k | Code-as-action. |
| **Letta** (MemGPT) | Apache-2.0 | ~17k | Stateful runtime with tiered memory. **Doubles as memory layer.** |
| **Agno (Phidata)** | MPL-2.0 | ~39k | ~2µs instantiation; AgentOS for production. |
| **Atomic Agents** | MIT | ~3k | Pydantic-schema composability. |
| **DSPy** | MIT | ~22k | Declarative; MIPROv2/GEPA optimizers. **Build the planner with this**. |
| **BeeAI / Bee** (IBM/LF) | Apache-2.0 | ~3k | ACP-native; OTel telemetry → Phoenix. |
| **Lyzr** | Apache-2.0 | ~1k | Low-code enterprise. |
| **LiteLLM** | MIT | ~17k | Universal LLM router/proxy. **Highly recommended adjacent infra.** |
| **LangChain core** | MIT | ~100k | Tools/integrations glue; legacy AgentExecutor deprecated. |
| **Griptape** | Apache-2.0 | ~2k | Modular Drivers abstraction. |
| **AgentScope** (Alibaba) | Apache-2.0 | ~16k | Multi-agent platform; native OTel + MCP/A2A. |
| **MetaGPT** | MIT | ~57k | Software-company multi-agent. |
| **ChatDev** | Apache-2.0 | ~28k | DevAll 2.0 zero-code multi-agent. |
| **Open Interpreter** | **AGPL-3.0** | ~60k | Local code-execution agent. AGPL caution. |
| **Aider** | Apache-2.0 | ~30k | CLI pair-programming. |
| **OpenHands** (OpenDevin) | MIT (core) | ~62k | Open SWE-Bench-Verified topper at ~53%. |

## 15. Observability and tracing

- **LangSmith** — closed source; native LangGraph; OTel export Mar 2025.
- **Helicone** (Apache-2.0, ~5k★) — proxy-based, one-line baseURL change. Acquired by Mintlify (maintenance mode).
- **Langfuse** (MIT, ~19k★) — **strong default**; OTel-native, framework-agnostic, self-hostable.
- **Phoenix** (Arize) — Elastic License 2.0 (not OSI), OpenInference/OTel.
- **Arize AX** — enterprise SaaS built on Phoenix.
- **OpenTelemetry GenAI semconv** (Apache-2.0) — v1.37+ standard; Datadog native; instrument once, swap backends.
- **Future AGI** — commercial eval+observability.
- **W&B Weave** (Apache-2.0) — decorator-based.
- **Braintrust** — eval-first commercial.
- **Lunary** (Apache-2.0, ~1k★) — lightweight Langfuse alt.
- **HoneyHive** — HITL annotation focus.
- **Galileo** — enterprise (ChainPoll, Luna eval models).
- **Comet Opik** (Apache-2.0, ~9k★) — 7–14× faster than Phoenix/Langfuse claimed.
- **OpenLLMetry / Traceloop** (Apache-2.0, ~6k★) — OTel auto-instrumentation; **vendor-neutral pick**.
- **LangWatch** (MIT, ~1k★) — DSPy-style optimization.
- **Datadog LLM Observability** — native OTel GenAI ingestion.
- **New Relic AI Monitoring**.

## 16. Memory / persistence layers

- **mem0** (Apache-2.0, ~48k★) — hybrid vector+graph+KV; self-edits on conflict; ~80% prompt-token reduction. Mem0g graph features behind $249/mo.
- **Letta / MemGPT** (Apache-2.0, ~17k★) — OS-tiered memory (core/archival/recall); ~83.2% LongMemEval. **Build agent on it for full stateful runtime.**
- **Zep / Graphiti** (Apache-2.0; Zep CE open, Cloud commercial) — **temporal knowledge graph** (~71.2% LongMemEval). **Best for cross-scan temporal reasoning.**
- **Cognee** (Apache-2.0, ~3k★) — ECL pipeline → vector + graph KG.
- **Vector stores:** Chroma (Apache, ~17k) · Qdrant (Apache, ~22k, Rust) · Weaviate (BSD-3, ~11k) · Pinecone (closed) · Milvus (Apache, ~30k) · LanceDB (Apache, ~6k, embedded columnar) · **pgvector** (Postgres License, ~14k — easiest if Postgres is in stack).
- **Memori** (Apache-2.0, ~5k★) — SQL-backed memory.
- **A-MEM** (Apache-2.0, ~1k★) — Zettelkasten-inspired dynamic linking.
- **MemoryBank** — Ebbinghaus forgetting; sporadic.
- **Generative Agents memory pattern** (Apache-2.0, ~20k★, Park et al.) — pattern, not library: stream + recency/importance/relevance + reflection.
- **Memary** (MIT, ~2k★) — local-first w/ Ollama + Neo4j.
- **MemoryScope** (Apache-2.0, Alibaba).
- **CharacterAI memory** — proprietary; reference only.
- **LangMem** (LangChain, MIT) — episodic + semantic + **procedural memory** (agent rewrites its own system instructions). Pluggable storage. **Natural pairing with LangGraph for evolving heuristics.**
- **Redis Agent Memory Server** (MIT) — sub-ms retrieval; semantic + keyword + hybrid; MCP server; OpenAPI.
- **Motorhead** (Apache-2.0, ~900★) — superseded by official Redis Agent Memory Server.

## 17. Open standards

**Chain identity:** CAIP-2, CAIP-10 (CC0, ChainAgnostic).
**EVM:** EIP-712 typed data · EIP-2612 permit · EIP-3009 transferWithAuthorization (USDC/EURC; **foundational for x402**) · ERC-4337 AA · **ERC-7715 wallet permissions / session keys** (draft, MetaMask Delegation Toolkit) · ERC-7857 iNFT (draft, 0G Labs).
**Agent identity:** **ERC-8004 Trustless Agents** (Identity ERC-721 / Reputation / Validation; mainnet Jan 29, 2026 across 20+ networks; authored by MetaMask + EF + Google + Coinbase).
**Payments:** **HTTP 402 / x402** (Apache-2.0; x402 Foundation = Coinbase + Cloudflare since Sept 2025; 75M+ tx by early 2026).
**Agent comms:** Anthropic **MCP** (MIT, donated to Linux Foundation Agentic AI Foundation) + MCP Authorization spec (OAuth 2.1 + DCR + PKCE) · Google **A2A** (Apache-2.0, donated to LF) · Cisco **AGNTCY** (Apache-2.0, LF — OASF + ACP + Decentralized Agent Directory + DID + SLIM gRPC + observability) · IBM **ACP** (Apache-2.0, merging into A2A).
**Security frameworks:** **OWASP LLM Top 10 2025** · **OWASP Agentic Apps Top 10 2026** (ASI01–ASI10 — Goal Hijack/Identity/Tool Misuse/Delegated Trust/Memory Poisoning/Cascading/Supply Chain/Resource Exhaustion/Unsafe Tool Exec/Rogue Agents) · **OWASP Agentic Skills Top 10 (AST10)** · OWASP API Top 10 (2023) · OWASP ASVS v5 · **MITRE ATLAS v5.4** (16 tactics, 84 techniques, STIX 2.1 export) · MITRE ATT&CK · **NIST AI RMF 1.0 + AI 600-1 Generative profile** + **NIST AI 100-2 e2025 Adversarial ML Taxonomy** · **ISO/IEC 42001** (certifiable) · ISO/IEC 23894 risk · **EU AI Act 2024/1689** (Art. 9/11/12/15) · ENISA AI Threat Landscape · CSA AI Controls Matrix (243 controls, 18 domains).
**Identity / auth:** W3C DID v1.1 (Candidate Rec March 2026) · IETF GNAP RFC 9635 (Oct 2024) · SIWE / ERC-4361.
**AIVSS** — Veracode-led AI vulnerability scoring extension to CVSS for LLM Top 10 findings.

## 18. Commercial AI security competitors

**Red-team-first:** **Mindgard** (Lancaster spinout, $11.6M, ATLAS-mapped DAST-AI — closest analog) · **SplxAI** (Croatia/US, $7M; **Agentic Radar** Apache-2.0 + commercial platform) · **Patronus AI** ($20M Series A; Lynx hallucination judge; Generative Simulators) · **Adversa AI** (Tel Aviv 2019, 300+ techniques) · **TrojAI** (NB/Boston; Detect + Defend) · **WithSecure / Reversec Labs** (**Spikee** OSS).
**Detection & response (M&A):** **HiddenLayer** (AISec 2.0 + AIDR + Auto Red Team + Model Scanner; M12, IBM, Capital One backers) · **Robust Intelligence → Cisco AI Defense** (Sept 2024 ~$400M; AI Firewall + algorithmic red team + Talos intel) · **CalypsoAI → F5** ($180M; Inference Perimeter/Red Team/Defend/Observe) · **Protect AI → Palo Alto Prisma AIRS** (~$700M April 2025; **Recon** 450+ attacks; **Layer** runtime; **Guardian** model scan; OSS: **ModelScan, NB Defense, LLM Guard, Vulnhuntr, AI Exploits**; runs **huntr** AI/ML bug bounty) · **Lakera → Check Point** (Guard runtime + Red continuous + **Gandalf** CTF + b3 benchmark).
**Agent governance / AISPM:** **Zenity** (Gartner "Company to Beat in AI Agent Governance") · **Noma Security** ($132M; Agentic Risk Map; 80+ integrations) · **WitnessAI** ($90M; intent-based detection; MCP tracking) · **Operant AI** (Agent Protector + 3D Defense + MCP discovery) · **Straiker AI** (Ascend AI red teamer; Defend AI runtime trained on millions of agent traces; **STAR Labs** found Perplexity Comet zero-click Drive wipe) · **Apex → Tenable** (~$100M May 2025) · **Aim Security** (acquisition rumors) · **Lasso Security** (acquisition rumors).
**Guardrail / prompt inspection:** **Pangea → CrowdStrike** (AI Guard 12+ detectors + Prompt Guard 99% efficacy claim) · **Prompt Security → SentinelOne** ($250M) · **Arthur Shield** (LLM firewall; Humana/DoD/3-of-top-5-US-banks) · **WhyLabs LangKit** (Apache-2.0; **company wound down**, OSS lives) · **Holistic AI** (governance-leaning).
**Data governance / discovery / trust:** **Cranium AI** ($32M; AI Card; Gartner Cool Vendor) · **Knostic** (OpenAnt LLM-based vuln discovery; coding-agent focus — closest competitor to your positioning) · **DeepKeep** · **Credal AI** · **Securiti AI**.
**Services boutiques:** **Trail of Bits** (ODD framework; DARPA AIxCC; OSS Differ) · **Bishop Fox** (**Cosmos AI** AI-powered pentest with HITL — direct competitor) · **NCC Group**.
**Observability w/ security layer:** **Datadog LLM Observability + AI Agent Monitoring + AI Guard + Bits AI Security Analyst + MCP Server**.
**App-sec adjacents:** **Snyk AI** (DeepCode + Snyk Code; AI Trust Platform) · **Veracode AI** (AIVSS investigation).

## 19. CTF, vulnerable-target suites, and benchmark labs

- **Damn Vulnerable LLM Agent (DVLA)** — github.com/ReversecLabs/damn-vulnerable-llm-agent (MIT, ~363★) — ReAct LangChain banking chatbot; Thought-injection + UNION-SQLi flags. **Direct CTF target for ReAct-agent attacks.**
- **Damn Vulnerable MCP Server (DVMCP)** — github.com/harishsg993010/damn-vulnerable-MCP-server (MIT) — **10 graded MCP-specific challenges**: prompt injection, tool poisoning, excessive permissions, rug-pull, tool shadowing, indirect PI, token theft, malicious code execution, RCE, multi-vector. **Primary first-evaluation target.**
- **appsecco/vulnerable-mcp-servers-lab** — complement: filesystem path-traversal + RCE, indirect PI over local stdio AND remote HTTP+SSE, secrets/PII, untrusted Wikipedia fetch.
- **DVAIA** — github.com/genbounty/DVAIA-Damn-Vulnerable-AI-Application (MIT) — Flask/Ollama/Qdrant; Direct/Document/Web/RAG/Template/Multimodal panels + 6-tool ReAct agentic panel.
- **DamnVulnerableLLMProject** (harishsg993010) — Replit-hosted LLM CTF.
- **Gandalf / Lakera** — gandalf.lakera.ai — 7 levels classic + Reverse + Adventure + Mosaic + Donjon + **Agent-Breaker** (MCP/agentic levels, file edits, OmniChat MCP exploitation). 9M+ interactions, 200k+ users.
- **AI Goat** (Orca Security) — github.com/orcasecurity-research/AIGoat (Apache-2.0, ~600★) — Terraform AWS toy-store mapping to OWASP ML Top 10 (supply-chain, data poisoning, output integrity).
- **AI Village CTFs** (DEFCON) — DEFCON 30 Kaggle 22 challenges; DEFCON 31 GRT 2,244 hackers × 8 LLMs × 21 topics, 17K conversations; DEFCON 32 GRT-2 model-card flaw discovery.
- **Microsoft AI Red Team** — PyRIT framework (above).
- **HackTheBox AI challenges** + **Dragos OT CTF 2025** (CAI hit Top-30 Spain).
- **TryHackMe AI rooms** (Intro to AI, Prompt Injection, Adversarial AI).
- **Immersive Labs prompt-injection** (10 levels), **Wiz Prompt Airlines**, **Snyk AI Learn**.
- **OWASP Juice Shop** (MIT, ~11k★) — sanity-check non-AI target before AI bugs.
- **Awesome-LLM-Agent-Security** discovery: OSU-NLP-Group/AgentSafety, zhangxjohn/LLM-Agent-Benchmark-List, philschmid/ai-agent-benchmark-compendium.

## 20. MCP server frameworks (build vulnerable benchmark targets)

- **modelcontextprotocol/python-sdk** (MIT/Apache-2.0; FastMCP 1.0 incorporated) — official.
- **modelcontextprotocol/typescript-sdk** (Apache-2.0/MIT) — official.
- **fastmcp** (jlowin → PrefectHQ) — Apache-2.0; **70% of MCP servers run some FastMCP version**; v3.0 GA with Components/Providers/Transforms; ~1M downloads/day. **DVMCP uses it.**
- **modelcontextprotocol/servers** (MIT) — Anthropic reference: Everything, Fetch, Filesystem, Git, Memory, Sequential Thinking, Time. **Use as known-good baselines AND CVE targets** (mcp-server-git had a 2025 triple-CVE chain).
- **mcp-go** (mark3labs) — MIT, ~8.6k★, de facto Go SDK.
- **modelcontextprotocol/rust-sdk** (rmcp) — MIT/Apache.
- **LiteMCP** — MIT, **officially deprecated** by author.
- **xmcp** (basementstudio) — TS with file-system routing + auth plugins.
- **golf-mcp** (golf-mcp/golf) — Python, atop FastMCP 2.11+; auto-discovery; built-in JWT/OAuth/API-key + telemetry.
- **mcp-lite** (fiberplane) — TS zero-runtime-dep; runs anywhere Fetch API exists.
- **Smithery SDK + CLI** — **largest hosted MCP registry (2,000+ servers)**. Use as source for real-world targets.
- **Test harnesses:** Python `mcp` client · `@modelcontextprotocol/sdk` · mark3labs/mcp-go/client · **mcphost** (mark3labs CLI host) · **MCP Inspector** (`@modelcontextprotocol/inspector`) · **mcp-cli** (wong2).

---

## Recommended stack synthesis for the hackathon build

**Agent core:** Build on **LangGraph** (durable persistent state + HITL + branching for scan logic) instrumented via **OpenLLMetry → Langfuse** (self-hosted OSS); planner compiled with **DSPy**; **LiteLLM** in front for cost/fallback. Memory: **pgvector** for embeddings + **LangMem** procedural memory for evolving heuristics + **Graphiti** for temporal facts about targets across scans.

**Pentest core:** Lift **PyRIT** orchestrator pattern + **garak** probe taxonomy + **FuzzyAI** `rest/http.raw` attacks + **HouYi** 3-component / 3-phase auto-PI loop + **Spikee** seed-document × jailbreak × instruction generator + **WhistleBlower** prompt-extraction recon. Wrap **promptmap2** + **promptfoo** + **Snyk mcp-scan** + **Cisco mcp-scanner** + **qsag-core** as auxiliary engines. Fire **nuclei** + **httpx** + **katana** for surface mapping.

**Sandboxing:** **e2b** (Firecracker) for unknown-target probes; **zerobox** for credential-scoped operations; **Inspect AI** harness for benchmark runs.

**Payments + identity:** **coinbase/x402** TS+Python SDKs; **PolicyLayer** mandatory spend caps; pay through **xpaysh agent-kit** with **PaySentry MockX402 sandbox** for testing. Identity: `<agent>.base.eth` via Coinbase Basenames + **ERC-8004** registration with `agentURI` JSON.

**Onchain:** **EAS contracts + SDK** on Base Sepolia for finding attestations (schema ~ `bytes32 cveId, uint8 severity, string evidenceURI, address target, bytes32 zkProofURI`); **Safe** holding the bounty pool with **Safe Module** enforcing per-finding/per-author payout caps; **Hats Protocol** encoding module-author/triage/agent-operator roles; reference `HackFirstBountyLater` design for the bounty escrow.

**Benchmarks to evaluate against:** DVMCP (10 graded MCP vulns) + appsecco lab + DVLA + Gandalf Agent-Breaker for online MCP-attack practice + AgentDojo + WASP + Cybench + BountyBench (real dollar impact) + InjecAgent. Run all through **HAL Harness**.

**Reporting taxonomy:** Map every finding to **OWASP Agentic Top 10 2026 (ASI01–ASI10)** + **OWASP LLM Top 10 2025** + **MITRE ATLAS v5.4** technique IDs + **NIST AI 100-2 e2025**. Cite **EU AI Act Art. 9/11/12/15** for European targets and **NIST AI 600-1** for US compliance posture.

**License hygiene watchlist:** Avoid direct code lifts from AGPL projects (AgentDojo, Vulnhuntr, trufflehog, Daytona, Open Interpreter, Coder/Gitpod), GPL (EasyJailbreak, sqlmap, Isolate), CC-BY-NC (LLAMATOR, SecAlign, BeaverTails, Do-Not-Answer, ALERT, ToxicChat, PKU-SafeRLHF), OpenRAIL (AmpleGCG), Elastic License 2.0 (Phoenix, Mastra parts), and proprietary/closed (Claude Agent SDK). MIT/Apache/BSD picks dominate the recommended-integration list above and are safe to wrap or extend.

**Total catalogued:** ~270 distinct items spanning all 20 categories; counts per category — Cat 1: 40 · Cat 2: 16 · Cat 3: 15 · Cat 4: 23 · Cat 5: 27 · Cat 6: 70+ · Cat 7: 25 · Cat 8: 18 · Cat 9: 12 · Cat 10: 14 · Cat 11: 9 · Cat 12: 25 · Cat 13: 26 · Cat 14: 28 · Cat 15: 17 · Cat 16: 16 · Cat 17: 25+ · Cat 18: 30+ · Cat 19: 14 · Cat 20: 12.