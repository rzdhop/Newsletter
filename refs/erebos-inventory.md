# Erebos-Zero — technique inventory

Source of truth: <https://github.com/rzdhop/Erebos-Zero> (public, 98 commits).

This file drives topic selection for Parties 02 and 03. The generator reads it
before choosing a subject and applies the rule in `brief.md`:

> A technique already implemented in Erebos-Zero is **not** a valid deep-dive
> subject. It may be referenced as prior work, in one sentence, with a link.
> Deep-dives go to techniques the operator has *not* built yet.

The point is not novelty for its own sake. Writing 2 600 words explaining
Hell's Gate to someone who has already implemented Hell's Gate is the exact
"hollow content" failure the design handoff forbids.

Re-read the repository README at the start of every run: it changes, and a
stale inventory would send the newsletter back over ground already covered.

---

## Implemented — reference only, never a deep-dive subject

### Loaders
| Technique | Note |
|---|---|
| EarlyBird APC injection | thread queuing before execution |
| Process injector, 4 escalating levels | custom `GetProcAddress` (manual EAT/PEB parsing), XORed constants, indirect syscall, basic anti-VM, basic anti-debug |
| Basic DLL injection | standard remote thread loading |
| sRDI — shellcode Reflective DLL injection | converting DLLs to PIC |
| Function stomping injection | overwriting legitimate function bodies |
| Mapping injection | shared sections, no `WriteProcessMemory` |
| Thread hijacking | redirecting RIP/EIP contexts |

### Misc
| Technique | Note |
|---|---|
| PPID spoofing | breaking process-tree analysis |
| Process argument spoofing | masking CLI in ProcMon |
| IAT hiding | import hashing via DJB2 |
| Registry stager | fileless shellcode storage |

### Bypass — EDR
| Technique | Note |
|---|---|
| Direct syscall | manual SSN transition |
| Indirect syscall | stealthy return address |
| Halo's Gate | unhooked-neighbour SSN recovery |
| Hell's Gate | dynamic EAT SSN extraction |
| Dynamic SSN retrieval | sorting `Zw*` functions |
| VEH AMSI bypass | hardware-breakpoint interception |

### Bypass — KASLR
| Technique | Note |
|---|---|
| Cache prefetch side-channel | timing attack on kernel |
| `NtQuerySystemInformation` | system module leak |

### C2
| Technique | Note |
|---|---|
| V.1 (legacy) | basic modular beaconing |
| V.2 (advanced) | StealthCall unified stack/syscall engine, call-stack spoofing, memory-resident PE loader |

### Stagers
| Technique | Note |
|---|---|
| Basic HTTP stager | WinHttp payload fetching |

---

## Not implemented — priority deep-dive candidates

Ordered roughly by adjacency to what already exists, so each subject builds on
the operator's current codebase rather than starting from nothing.

| Candidate | Why it fits | Adjacent to |
|---|---|---|
| **BOF loader / COFF loading** | explicitly flagged by the operator as the gap. Natural next step after a PE loader — parse relocations, resolve `__imp_` symbols, execute in-place | C2 V.2 PE loader |
| Sleep obfuscation (Ekko, Foliage, Cronos) | encrypts the beacon at rest; the missing half of a stealthy C2 | C2 V.2 |
| Module stomping / DLL hollowing | writes into a legitimately-loaded module's `.text` | function stomping |
| Hardware-breakpoint hooking (Dr0-Dr3) | generalises the VEH trick already used for AMSI | VEH AMSI bypass |
| ETW patching and ETW-Ti evasion | the telemetry channel that survives user-mode unhooking | direct/indirect syscall |
| Kernel callback removal | `PsSetCreateProcessNotifyRoutine`, `ObRegisterCallbacks` | KASLR leak work |
| Fresh `ntdll` mapping for unhooking | reload a clean copy from disk or KnownDlls | Halo's/Hell's Gate |
| TLS callback abuse | pre-`main` execution, defeats naive entry-point breakpoints | loaders |
| Syscall stack spoofing refinements | synthetic frames that survive `RtlWalkFrameChain` | StealthCall |
| Windows Filtering Platform callouts | traffic interception without a hooking driver | stagers |
| Hardware: PCILeech / DMA attacks | the operator asked for hardware topics | — |
| Hardware: SPI flash dumping, UART/JTAG | entry-level hardware, good weekend material | — |
| Web: HTTP request smuggling (CL.0, TE.CL) | operator asked for advanced web only | — |
| Web: SSRF to cloud-metadata chains | advanced, reproducible in a lab | — |
| Web: prototype pollution to RCE | advanced JS exploitation | — |

---

## Topic-selection procedure

1. Fetch the Erebos-Zero README; refresh the implemented list above if it moved.
2. Read `state/topics-index.json` — anything covered in the last 90 days is out.
3. Prefer a candidate from the table above whose prerequisite is already
   implemented: the deep-dive then reads as the operator's next commit, not as
   a disconnected tutorial.
4. Alternate domains between Partie 02 and Partie 03. Two Windows maldev
   deep-dives in one issue is a weaker edition than one maldev plus one
   hardware or web subject.
