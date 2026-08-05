# Erebos-Zero — coverage filter

Source of truth: <https://github.com/rzdhop/Erebos-Zero> (public, 98 commits).

**What this file is for.** It is a deduplication filter, and nothing else. The
reader has already built the techniques listed below, so an issue that explains
one of them to him is wasted words. Writing 2 600 words on Hell's Gate for
someone who has implemented Hell's Gate is the exact "hollow content" failure
the design handoff forbids.

**What this file is not for.** It does not select subjects. It never did a good
job of it: choosing a topic because the reader has not built it yet turns the
newsletter into a build queue for one codebase, which is both a narrower
publication and a worse one. Subjects come from the field — see the procedure
at the bottom.

Re-read the repository README at the start of every run: it changes, and a
stale list would send the newsletter back over ground already covered.

---

## Implemented — reference only, never a deep-dive subject

A technique in this table may be **mentioned** — one sentence, with a link, as
prior work or as context for something else. It is never the subject.

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

## Domains in scope

The newsletter is offensive security, full stop. No defensive reframing is
required and no detection section is mandatory. These are the domains a
deep-dive can come from:

- **Windows maldev** — loaders, injection, evasion, C2 internals, kernel.
- **Hardware** — DMA and PCILeech, SPI flash, UART/JTAG, side-channel, glitching.
- **Web** — advanced only: request smuggling, SSRF chains, prototype pollution,
  deserialisation, cache poisoning.
- **Platform and kernel research** — Windows/Linux/macOS internals, hypervisor,
  firmware, mobile.

Parties 02 and 03 must come from different domains. Two Windows-maldev
deep-dives in one issue is a weaker edition than one maldev plus one hardware
or web subject.

---

## Topic-selection procedure

1. **Start from what the field published.** The candidate pool is the research
   surfaced in Step 2 of the runbook — this week's papers, talks, advisories
   and write-ups from the labs in `sources.yaml`, plus the archive when the
   week is thin. The subject is chosen because the published work is
   technically interesting, not because of any gap in any codebase.
2. **Drop anything covered in the last 90 days** — `state/topics-index.json`.
3. **Drop anything in the implemented table above.** This is the filter's whole
   job: no rehashing what the reader already knows.
4. **Prefer the subject with the better primary source.** A technique with a
   detailed public write-up, a paper, or a documented PoC repository supports a
   deeper issue than one known only from a vendor summary. Depth is bounded by
   what the source actually establishes — where you go past it, you are
   inferring, and inference gets the `warning` component.
5. **Alternate domains** between Partie 02 and Partie 03.
6. Fetch the Erebos-Zero README at the start of the run and refresh the
   implemented table above if it moved.
