# Бектест верифікатора на Opus 5.5 — окремі агенти (2026-10-12)

Ті самі 8 кейсів і той самий промпт v2 (cases-v2.md; verifier-prompt.md).
Кожен кейс — окремий агент (Agent tool, model opus, general-purpose), бачив
лише свої файли-джерела з sources/. Запит користувача 2026-10-12: «так, робимо
ланцюжок з бектестом Opus» (запасна ланка verify-before-show, коли DeepSeek і
NVIDIA не відповідають). Сесія e3a33280.

Прогін лише №1 (хвиля 1). Протокол вимагає двох; хвилю 2 відкладено
2026-10-13 — див. кінець файлу.

| Кейс | Очікую | №1 | Ключова цитата (grep -F, збігів) |
|------|--------|----|----------------------------------|
| N-E1 | НІ | НІ | 'human/agent-readable mirror of current baton' — 1 |
| N-E2 | НІ | НІ | 'centralized verification reduces trace-level error amplification from 17.2' — 1 |
| N-E3 | НІ | НІ | 'most coding tasks involve fewer truly parallelizable tasks than research' — 1 |
| N-E4 | НІ | НІ | 'an optional compact handoff note keeps the thread coherent' — 1 |
| N-K1 | ТАК | ТАК | 'next: args.next ?? prev.next ?? [],' — 1 |
| N-K2 | ТАК | ТАК | 'multi-agent systems use about 15× more tokens than chats' — 1 |
| N-K3 | ТАК | ТАК | 'architectures without centralized verification…' — 1 |
| N-K4 | ТАК | ТАК | 'speaks Anthropic' — 1 |

Упіймано 4 з 4, хибних тривог 0 з 4 (за одним прогоном). Ціна: 247 825
токенів агентів (ліміт Pro, не гроші), 15–34 с на агента. Того ж дня обидві
безкоштовні ланки збоїли: BazaarLink ECONNRESET 3 з 6, NVIDIA ETIMEDOUT.

## Чому хвилю 2 відкладено (2026-10-13)
Усі три перевіряльники (DeepSeek flash — results-v2.md, gpt-oss — results-nvidia.md,
Opus — тут) дали однаковий результат 4/4 і 0 хибних: набір cases-v2 занадто
легкий і їх не розрізняє (стеля). Другий прогін перевірив би лише
стабільність на тих самих легких кейсах. Питання користувача: чи тест не
«пустий» — наступний крок — складніші кейси (cases-v3), рішення за ним.
