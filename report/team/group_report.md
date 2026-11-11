# Báo cáo nhóm — AISAFETY — Day 03 Research Agent Tool Eval

## 1. Thông tin nhóm

- Nhóm AISAFETY, lớp L3B; thành viên và phân công: [TEAM.md](../../TEAM.md).
- Provider/model v0–v4: OpenRouter / openai/gpt-4o-mini.

## 2. Mục tiêu và cách tiếp cận — PHẦN A: Giới thiệu agent

### A1. Agent này làm được gì

Agent tìm tin web/social, đọc URL và paper, tra chính sách nội bộ, xử lý danh sách và tổng hợp kèm nguồn. Gửi Telegram cần xác nhận; UI có bước xem nội dung và nút xác nhận/hủy riêng.

**Cách chạy UI:** từ root repo, tạo venv nếu chưa có bằng lệnh `uv venv starter_v0/.venv`, cài dependency bằng `uv pip install --python starter_v0/.venv/Scripts/python.exe -r starter_v0/requirements.txt`, đặt biến môi trường DAY03_UI_VERSION=v4, rồi chạy `starter_v0/.venv/Scripts/python.exe -m streamlit run starter_v0/app.py`. Cấu hình starter_v0/.env theo [hướng dẫn](../../docs/TOOL-SETUP.md). Streamlit đã có trong [requirements.txt](../../starter_v0/requirements.txt). Không đưa secret vào Git.

**Link dùng thử:** [AISAFETY Streamlit](https://k5-l3b-day03-aisafety-researchagenttooleval-6ftuhztxnienlwuu6g.streamlit.app/).

Kiểm tra HTTP ngày 10/11/2026 trả mã 200 và trang Streamlit trả về shell. UI local chạy kịch bản bằng provider thật qua Streamlit AppTest, 0 exception; chưa chứng minh WebSocket/chat công khai hoạt động, deploy khớp v4, hoặc có người ngoài nhóm nghiệm thu link. Vì chưa push v4, không dùng link deploy làm bằng chứng artifact cuối.

### A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | Hỏi thông tin còn thiếu hoặc xác nhận | Không |
| timeline | Lấy bài từ một tài khoản cụ thể | Không |
| social_search | Tìm bài social theo chủ đề | Không |
| lookup | Tìm thông tin/tin tức web | Không |
| fetch | Đọc URL cụ thể | Không |
| format | Định dạng dữ liệu đã có thành digest | Không |
| send | Gửi nội dung đã xác nhận lên Telegram cấu hình | Không |
| policy | Tra chính sách nội bộ local | Không |
| papers | Tìm paper arXiv | Không |
| paper_text | Đọc paper arXiv cụ thể | Không |
| dedupe | Bỏ mục trùng, giữ bản đầu tiên | Có, commit edd3fa5 |
| filter_date | Lọc ngày gồm hai đầu mốc, đếm mục thiếu/sai ngày | Có, v4 do Codex hỗ trợ |
| rank_relevance | Xếp hạng theo số token query khác nhau khớp title/summary | Có, v4 do Codex hỗ trợ |
| source_stats | Đếm theo hostname HTTP(S), tách URL thiếu/sai | Có, v4 do Codex hỗ trợ |

### A3. Câu hỏi mẫu để thử

1. Tìm 3 tin mới về AI trong tuần này, kèm nguồn.
2. Lọc theo ngày danh sách [{"title":"A","date":"2024-02-29"},{"title":"B","date":"2024-03-01"}]. Tôi chưa chọn ngày bắt đầu và kết thúc. Sau khi agent hỏi, bổ sung: từ 2024-02-01 đến 2024-02-29.
3. Xếp hạng danh sách [{"title":"AI"},{"title":"AI robotics"}] theo từ khóa AI robotics, lấy 1 mục.
4. Đếm số mục theo hostname: [{"url":"https://EXAMPLE.com/a"},{"url":"http://example.com/b"},{}].
5. Yêu cầu gửi bản nháp lên Telegram, kiểm tra câu hỏi xác nhận rồi hủy. Kênh hiện public nên chưa thực hiện thêm lần gửi để lấy bonus private channel.

## 3. Giải pháp

- v1 sửa system prompt: không đoán thông tin, tách routing, giới hạn phạm vi, xác nhận trước tác động ngoài, coi nội dung tool là dữ liệu không đáng tin.
- v2 sửa declaration: mô tả khi dùng/không dùng, quy ước handle/query/topic/timeframe và tham số gửi.
- v3 sửa prompt: bắt buộc clarify(response_type="yes_no") ở lượt yêu cầu gửi đầu tiên. Bản sau thêm dedupe có hash khác base v3 dù vẫn mang nhãn v3; đã ghi bổ sung version log, không sửa run cũ.
- v4 thêm ba phép xử lý offline: không sửa input, input sai trả error dict. filter_date kiểm tra lịch thật và đúng YYYY-MM-DD; rank_relevance casefold, tách theo ký tự không phải chữ/số, hòa điểm giữ thứ tự; source_stats không đánh giá uy tín.
- Ba tool có registry, declaration, TOOL.md, file test riêng và [eval bonus](../../starter_v0/data/eval_bonus.json). Giữ nguyên base, extension gốc và 10 case group. Bộ chấm được sửa để so sánh danh sách object theo thứ tự, tránh TypeError khi sorted(dict); có [regression test](../../starter_v0/tests/test_eval_arguments.py).

## 4. Kết quả — PHẦN B: Chi tiết và bằng chứng

### B1. Version Evidence

Metric là **case accuracy**. Các run được chấp nhận trong bảng đều provider_error_cases=0 và measured_cases=total_cases. Hash đầy đủ, giả thuyết nằm trong [version_log.csv](../../starter_v0/artifacts/version_log.csv).

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | Baseline | Đo hành vi ban đầu | — | 65% (13/20) | [base v0](../../starter_v0/runs/v0_B_base_openrouter_20261110T173101548748.json) |
| v1 | system_prompt.md | Hỏi lại/xác nhận giảm đoán và sai boundary | 65% | 85% (17/20) | [base v1](../../starter_v0/runs/v1_B_base_openrouter_20261110T192815118469.json) |
| v2 | tools.yaml | Description và convention rõ giảm sai args | 85% | 95% (19/20) | [base v2](../../starter_v0/runs/v2_B_base_openrouter_20261110T193040378126.json) |
| v3 | system_prompt.md | Bắt buộc yes_no ở lượt gửi đầu tiên | 95% | 100% (20/20) | [base v3](../../starter_v0/runs/v3_B_base_openrouter_20261110T193430837841.json) |
| v3 sau dedupe | Prompt + tools | Route dedupe trên dữ liệu đã có | — | 100% (10/10 group) | [group lịch sử](../../starter_v0/runs/v3_B_group_openrouter_20261110T221819343346.json) |
| v4 | Prompt + tools, 3 tool mới | Mở rộng offline vẫn giữ routing base | 100% base | 100% (20/20) | [base v4](../../starter_v0/runs/v4_B_base_openrouter_20261110T231223951219.json) |
| v4 | Cùng artifact, group không đổi | Giữ routing nhóm khi tăng toolset | 100% group | 100% (10/10) | [group v4](../../starter_v0/runs/v4_B_group_openrouter_20261110T231141594846.json) |
| v4 | Cùng artifact, bonus riêng | Route 4 tool mới và hỏi thiếu mốc ngày | — | 100% (6/6) | [bonus v4](../../starter_v0/runs/v4_B_extension_openrouter_20261110T231122313648.json) |

Base v3: v3+pfddaf2ba05d4+t82590deaad13; group sau dedupe: v3+pe7485b4afc9c+t7c117d8bccc0. Không lấy 100% base v3 để chứng minh bản dedupe đã được đo base. Dataset extension gốc eval_research_extension.json không được chạy với v4; run bonus 6/6 dùng dataset eval_bonus.json riêng.

Ba run v4 và hai transcript cuối đều **v4+pdbd982b6c856+t45f38af86103**. Routing/argument/multiturn accuracy của cả ba run v4 đều 100%. Đây là một lượt đo mỗi suite, không phải độ tin cậy tổng quát. Eval chấm routing/args, không chấm chất lượng câu trả lời hay mọi lỗi tool: G10 có send đúng args nhưng trả lỗi thiếu token vì credential gửi đã chủ động tắt trong tiến trình.

[Run v4 lỗi môi trường](../../starter_v0/runs/v4_B_base_openrouter_20261110T230911407986.json) được giữ lại: 20 provider errors, 0/20 measured, **không hợp lệ để tính accuracy**; không diễn giải 0.0 trong JSON là điểm năng lực model.

### B2. Failure Analysis

Nguồn: [baseline v0](../../starter_v0/runs/v0_B_base_openrouter_20261110T173101548748.json). Failure ghi nhãn case trong JSON và sai lệch quan sát; không đổi nhãn lịch sử.

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R03_web_news_routing | wrong_tool; observed wrong_arg_value | lookup(query="AI news", news, day) | Query phải là AI | v2: core query |
| R08_out_of_scope | out_of_scope; unexpected_tool_call | send(text=đáp án nguyên hàm) | Bài toán phải no_tool | v1/v3: scope, send không phải kênh trả lời |
| R10_missing_handle | missing_info; missing_tool_call | timeline(screenname="sama") | Đoán tài khoản thay vì clarify | v1: không đoán người/tài khoản |
| R11_missing_url | missing_info; missing_tool_call | fetch(url="https://example.com/article") | Bịa URL thay vì clarify | v1/v2: cần URL rõ ràng |
| R12_confirm_before_send | wrong_boundary; missing_tool_call | send(text="Bản tin này") | Không hỏi xác nhận | v1/v3: clarify yes_no, chờ lượt sau |
| R13_parallel_web_and_tweets | wrong_tool; observed wrong_arg_value | lookup("AI news", day) + social_search("AI", Latest) | Query lookup sai, thiếu topic=news | v2: query và topic |
| R14_out_of_scope_coding | out_of_scope; unexpected_tool_call | send(text=mã Fibonacci) | Coding phải no_tool | v1/v3: no-tool boundary |

### B3. Team Eval Cases

[Dataset](../../starter_v0/data/eval_group.json) giữ đúng **5 single + 5 multi**, kết quả từ [group v4](../../starter_v0/runs/v4_B_group_openrouter_20261110T231141594846.json).

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| G01_news_today | Single: tin AI hôm nay | lookup, AI, news, day | PASS |
| G02_top_social_search | Single: top social | social_search GPT-5, Top | PASS |
| G03_explicit_url_fetch | Single: URL cụ thể | fetch đúng URL | PASS |
| G04_missing_account_clarify | Single: thiếu tài khoản | clarify, text | PASS |
| G05_dedupe_existing_results | Single: tool mới | dedupe danh sách đã có | PASS |
| G06_multiturn_account_fill | Multi: bổ sung người, giữ limit | timeline elonmusk, 5 | PASS |
| G07_multiturn_url_fill | Multi: bổ sung URL | fetch URL đã cung cấp | PASS |
| G08_multiturn_news_timeframe | Multi: đổi query, giữ ngày | lookup robotics, news, day | PASS |
| G09_multiturn_switch_to_web | Multi: social sang web | lookup OpenAI, news | PASS |
| G10_multiturn_send_confirmation | Multi: xác nhận gửi | send confirmed=true | PASS routing/args; không gửi thật |

### B4. Live Chat Evidence

Hai kịch bản dùng provider thật với input tự động, không phải mock hoặc phản hồi của người ngoài nhóm. [CLI](../../starter_v0/transcripts/v4_openrouter_20261110T231201448826.transcript.json) chạy qua chat.py; [UI](../../starter_v0/transcripts/v4_openrouter_47bebc6ecb21423abe67cddb790104c8.transcript.json) chạy app thật qua Streamlit AppTest. Cùng hash v4 tại B1.

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
| CLI 1 | Tra chính sách trích dẫn | policy | v4, CLI | Không có kết quả; không tính research thành công |
| CLI 2 → 3 | Thiếu mốc ngày → bổ sung | clarify → filter_date | v4, CLI | Hỏi lại rồi giữ A, bỏ B ngoài khoảng |
| CLI 4 → 5 | Gửi bản nháp → hủy | clarify yes_no → no tool | v4, CLI | Không gửi |
| UI 1 | Tìm 3 tin AI trong tuần, kèm nguồn | lookup | v4, UI | 3 mục kèm URL; chưa đánh giá độc lập từng nguồn |
| UI 2 → 3 | Thiếu mốc ngày → bổ sung | clarify + dedupe thừa → filter_date | v4, UI | Giữ A, bỏ B; lượt hỏi lại có gọi dedupe không cần thiết |
| UI 4 → 5 | Gửi bản nháp → xác nhận bằng chat | clarify → send bị UI giữ lại | v4, UI | Hiện nội dung, chờ nút xác nhận riêng |
| UI 6 | Bấm Hủy | Không gọi tool | v4, UI | cancelled, không gửi |

Hai kịch bản dùng provider thật; credential gửi Telegram đã tắt trong tiến trình kiểm tra. Transcript JSON là bằng chứng đối chiếu các lượt chat và trạng thái gửi.

### B5a. Required Evidence — Tool mới, unit test, UI

| Item | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| dedupe | [TOOL.md](../../starter_v0/tools/dedupe/TOOL.md), [3 test](../../starter_v0/tests/test_tools_todo.py) | Happy path, input sai, object sai; G05/X06 route đúng | Chỉ bỏ trùng theo URL/title |
| filter_date | [TOOL.md](../../starter_v0/tools/filter_date/TOOL.md), [test](../../starter_v0/tests/test_filter_date.py) | Biên ngày, năm nhuận, thiếu/sai ngày, khoảng sai, không sửa input | Không suy diễn ngày; invalid/ngoài khoảng đếm riêng |
| rank_relevance | [TOOL.md](../../starter_v0/tools/rank_relevance/TOOL.md), [test](../../starter_v0/tests/test_rank_relevance.py) | Unicode, token duy nhất, hòa điểm, input/limit sai | Lexical, không phải semantic relevance |
| source_stats | [TOOL.md](../../starter_v0/tools/source_stats/TOOL.md), [test](../../starter_v0/tests/test_source_stats.py) | Host lowercase, port/subdomain/IPv6, URL thiếu/sai | Không kiểm tra DNS/uy tín |
| Unit test | `cd starter_v0; pytest` | 149 passed, 14 skipped, 0 failed/error | 14 stub TODO vẫn skip; test offline |
| UI | [app.py](../../starter_v0/app.py), transcript UI ở B4 | 14 tool, 6 lượt live, 0 exception, hủy gửi | HTTP 200 không thay thế thử chat public |

Mỗi tool mới có ít nhất 3 test; ba tool bổ sung có 40 trường hợp test sau parametrization. Unit test bắt limit=True bị từ chối và ngày 2023-02-29 sai; eval routing không đảm bảo code xử lý được các input đó.

### B5. Bonus Evidence

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| Small Local Model | B7 | Hoãn | Không run, không nhận bonus |
| Hơn 3 tool mới | B5a, [bonus run](../../starter_v0/runs/v4_B_extension_openrouter_20261110T231122313648.json) | 4 tool đủ docs/registry/declaration/test và routing | Ba tool mới chưa commit; cần thành viên tự giải thích |
| Telegram thật sau xác nhận | [transcript lịch sử](../../starter_v0/transcripts/ui_openrouter_3c130f0306e04ffbb78ac38619b6d1b9.transcript.json) | Lượt 2 chờ xác nhận, lượt 3 confirmed=true, status=sent | Hash baseline, không phải v4; chưa đủ bằng chứng private channel |
| Test challenge qua regression | [test_send_errors.py](../../starter_v0/tests/test_send_errors.py), commit 037d5f0 | Giữ mô tả HTTP 400, HTTP 502 không JSON, che token, không retry | Mock không chứng minh gửi thật; không nhận nhánh 0 skipped |

Bug Telegram: raise_for_status() trước đây làm mất mô tả API như Bad Request: chat not found; sửa lấy description từ JSON lỗi nếu có, giữ status code và che token trong exception. Bốn regression test kiểm tra cả thành công cũ.

Telegram getChat xác minh kênh cấu hình trùng [@ai_slop_vip](https://t.me/ai_slop_vip), type=channel và có public username. **Chưa đáp ứng yêu cầu private channel** của RULES/RUBRIC. Không tự đổi privacy hoặc gửi thêm tin. Trạng thái private tại thời điểm transcript lịch sử cũng chưa được xác minh.

### B7. Small Local Model Challenge (bonus)

Hoãn theo ưu tiên đã chọn. Chưa có run local, chưa có so sánh cloud/local hay hai vòng tối ưu local. Không điền metric giả hoặc nhận bonus phần này.

## 5. Khó khăn và cách xử lý

- Pytest sandbox gặp lỗi quyền thư mục temp; chạy ngoài sandbox đạt 149 passed, 14 skipped, 0 failed/error, không sửa code để né lỗi môi trường.
- SDK import lỗi ArgsKwargs trong pydantic_core; cài lại dependency rồi đo lại. Giữ run lỗi 0/20 measured riêng với run hợp lệ.
- Bộ chấm cũ sorted() danh sách dict bị TypeError; 2 test fail trước sửa, sau sửa cả 3 regression test pass. Không đổi case gốc.
- CLI policy tiếng Việt không có kết quả: giới hạn retrieval local cần cải thiện, không che bằng routing 100%.
- Chưa xác minh deploy v4/người ngoài nhóm thử UI; Telegram public; chưa xác minh commit kỹ thuật riêng của Hoàn. Các mục này còn mở trước nghiệm thu.

## 6. Tổng hợp đóng góp

[Hoàng](2A202603952_NguyenPhiHoang.md): UI/session/confirmation/regression có commit 037d5f0. [Hoàn](2A202603972_NguyenCongHoan.md): xác minh được commit TEAM; phân công tool/bảng cần xác nhận thực tế. Chi tiết [TEAM.md](../../TEAM.md). Codex hỗ trợ code/báo cáo v4, không gán thay công cá nhân. Claude Code hoàn tất review độc lập qua Herdr: approve có điều kiện, không có Critical. Hai finding Important về việc thiếu đồng bộ remote và link tới evidence chưa được track đã được xử lý bằng fast-forward, hòa báo cáo và xóa folder evidence cùng liên kết. Reviewer cũng đề xuất minor: ghi chú tool call dedupe thừa trong B4, thêm test cho IDN/localhost/trailing dot, nói rõ extension gốc chưa chạy trên v4, và giải thích so sánh object args giữ nguyên hoa/thường; các ghi chú này đã được xử lý hoặc nêu rõ dưới đây.

## 7. Hạn chế và hướng cải thiện — B6. Reflection

- Prompt quyết định routing/scope/confirmation; declaration quy định cách dùng và args. Runtime UI cần khóa gửi độc lập vì tuân thủ prompt không phải cơ chế cấp quyền.
- Eval đo lượt chọn tool, multi-turn là context gộp; không thay thế live loop, chất lượng nguồn, hallucination, prompt injection hay UX. Cần review thủ công và kiểm tra người dùng thật.
- Một lượt đạt 100% không chứng minh ổn định qua nhiều lần/model. Vòng tiếp theo thử paraphrase, thiếu một mốc ngày, nhiều phép biến đổi nối tiếp và policy tiếng Việt; ghi metric thật kể cả giảm. Bộ chấm so sánh nguyên văn object trong danh sách, kể cả phân biệt hoa/thường, để kiểm tra việc model giữ đúng payload người dùng cung cấp.
- Hoàn thiện nghiệm thu public UI, phân công/commit cá nhân và điều kiện private channel trước khi kết luận đầy đủ CP1–CP5; local model hoãn.

## 8. Tài liệu tham khảo

- [CHECKPOINTS](../../CHECKPOINTS.md), [RULES](../../RULES.md), [RUBRIC](../../RUBRIC.md), [SUBMISSION](../../SUBMISSION.md).
- [Tool authoring](../../starter_v0/tools/README.md), [README starter](../../starter_v0/README.md), [version log](../../starter_v0/artifacts/version_log.csv).
- Source/run/transcript dẫn trực tiếp trong từng bảng; không dùng tài liệu capability làm bằng chứng kết quả đo.
