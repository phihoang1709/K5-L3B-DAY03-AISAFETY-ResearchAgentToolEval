# Báo cáo nhóm — Day 03 Research Agent Tool Eval

## 1. Thông tin nhóm

- Tên nhóm: AISAFETY
- Thành viên và phân công: xem [TEAM.md](../../TEAM.md)
- Provider/model dùng cho v0–v3: OpenRouter / `openai/gpt-4o-mini`
- Repo: https://github.com/phihoang1709/K5-L3B-DAY03-AISAFETY-ResearchAgentToolEval
- Nhánh và commit chốt hiện tại: `main` / `edd3fa5` (`feat: add dedupe tool and group evals`)

## 2. Mục tiêu và cách tiếp cận — PHẦN A: Giới thiệu agent

### A1. Agent này làm được gì

Research agent tìm thông tin trên web và mạng xã hội, đọc URL, tìm/đọc paper arXiv, tra cứu policy nội bộ, định dạng digest và gửi nội dung lên Telegram sau khi người dùng xác nhận.

**Cách chạy UI:**

```powershell
cd starter_v0
python -m streamlit run app.py
```

Dependency UI: `streamlit>=1.45,<2` trong `starter_v0/requirements.txt`.

**Link dùng thử:**

`http://127.0.0.1:8501` (local URL đã kiểm tra HTTP 200; chưa có public deployment).

### A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| `clarify` | hỏi lại khi thiếu thông tin hoặc cần xác nhận | không |
| `timeline` | lấy bài đăng gần đây của một tài khoản | không |
| `social_search` | tìm bài đăng theo chủ đề trên mạng xã hội | không |
| `lookup` | tìm kiếm web/news theo topic và timeframe | không |
| `fetch` | đọc nội dung một URL cụ thể | không |
| `format` | trình bày các item đã có thành digest | không |
| `dedupe` | loại bài trùng theo URL hoặc title, giữ thứ tự đầu tiên | có |
| `send` | gửi text lên Telegram sau xác nhận | không |
| `policy` | tìm trong policy nội bộ | không |
| `papers` | tìm paper/preprint trên arXiv | không |
| `paper_text` | tải và trích text từ paper arXiv | không |

### A3. Câu hỏi mẫu để thử

1. `Tin tức AI hôm nay có gì nổi bật?`
2. `Cho mình các tweet phổ biến nhất về GPT-5.`
3. `Tóm tắt bài viết này: https://openai.com/research/`
4. `Tóm tắt 5 tweet mới nhất của Elon Musk.`
5. `Đăng bản tin này lên Telegram giúp mình.`

## 3. Giải pháp

- `system_prompt.md` loại bỏ hành vi đoán handle/URL, yêu cầu `clarify` khi thiếu thông tin, định nghĩa routing, no-tool boundary và confirmation boundary cho hành động gửi.
- `tools.yaml` mô tả điều kiện dùng/không dùng, quy ước handle không có `@`, `topic`, `timeframe`, `search_type`, URL và `confirmed=true`.
- Thêm tool local `dedupe` trong `starter_v0/tools/dedupe/`; tool loại duplicate theo URL chuẩn hóa hoặc title chuẩn hóa, trả error dict cho input không hợp lệ.
- Thêm declaration, registry entry, 3 unit test và 10 group eval case.

## 4. Kết quả — PHẦN B: Chi tiết và bằng chứng

### B1. Version Evidence

Tất cả run dưới đây có `provider_error_cases == 0` và `measured_cases == total_cases`.

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline | Đo baseline trước khi sửa prompt/declaration | — | 0.65 | [v0](../../starter_v0/runs/v0_B_base_openrouter_20261110T173101548748.json) |
| v1 | `system_prompt.md` | Clarification và confirmation gate giảm lỗi thiếu thông tin/ranh giới | 0.65 | 0.85 | [v1](../../starter_v0/runs/v1_B_base_openrouter_20261110T192815118469.json) |
| v2 | `tools.yaml` | Declaration rõ hơn giảm sai argument và routing | 0.85 | 0.95 | [v2](../../starter_v0/runs/v2_B_base_openrouter_20261110T193040378126.json) |
| v3 | `system_prompt.md` | No-tool boundary và yes/no confirmation bắt buộc loại lỗi còn lại | 0.95 | 1.00 | [v3](../../starter_v0/runs/v3_B_base_openrouter_20261110T193430837841.json) |

Base v3 đạt `20/20`, `case_accuracy=1.0`, `tool_routing_accuracy=1.0`, `argument_accuracy=1.0`, `multiturn_accuracy=1.0`.

### B2. Failure Analysis

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R03 | `wrong_arg_value` | `lookup(query="AI news", topic="news", timeframe="day")` | query chứa từ phụ `news` | thêm convention query core subject |
| R08 | `out_of_scope` | `send(...)` | gọi tool cho bài toán ngoài phạm vi | thêm no-tool/scope boundary |
| R10 | `missing_info` | `timeline(screenname="sama")` | đoán người dùng khi thiếu handle | bắt buộc `clarify` |
| R11 | `missing_info` | `fetch(url="https://example.com/article")` | tự bịa URL | bắt buộc hỏi URL |
| R12 | `wrong_boundary` | `send(...)` | gửi trước xác nhận | bắt buộc `clarify(response_type="yes_no")` |
| R13 | `wrong_arg_value` | `lookup(query="AI news", ...)` + `social_search(query="AI")` | web query chưa chuẩn hóa | mô tả rõ query/topic trong declaration |
| R14 | `out_of_scope` | `send(...)` | biến yêu cầu coding thành hành động gửi | thêm rule không dùng `send` cho coding/meta |

### B3. Team Eval Cases

Run bằng [v3 group run](../../starter_v0/runs/v3_B_group_openrouter_20261110T221819343346.json) đạt 10/10.

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| G01 | news và timeframe hôm nay | `lookup(topic=news, timeframe=day)` | PASS |
| G02 | social Top search | `social_search(search_type=Top)` | PASS |
| G03 | URL cụ thể | `fetch` đúng URL | PASS |
| G04 | thiếu tài khoản | `clarify(response_type=text)` | PASS |
| G05 | route tới tool mới | `dedupe` | PASS |
| G06 | multi-turn map Elon Musk | `timeline(screenname=elonmusk, limit=5)` | PASS |
| G07 | multi-turn bổ sung URL | `fetch` đúng URL | PASS |
| G08 | carry topic news/timeframe | `lookup(query=robotics, topic=news, timeframe=day)` | PASS |
| G09 | chuyển social sang web | `lookup(query=OpenAI, topic=news)` | PASS |
| G10 | confirmation trước publish | `send(confirmed=true)` sau lượt xác nhận | PASS |

### B4. Live Chat Evidence

Hai transcript dưới đây có đủ 3 lượt và chứng minh luồng hỏi/preview/xác nhận hoặc hủy. Chúng được tạo với artifact UI trước bản prompt v3; transcript mới nhất `ui_openrouter_847ea278e15143688413db3929cacb72.transcript.json` có artifact group hiện tại nhưng chỉ có một lượt.

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
| 1 | `trường vinuni thành lập năm nào?` | `lookup` | `ui+peb1c8179815b+te69bc53ed884` | answered |
| 2 | `gửi vào tele cho tôi` | `send` | cùng transcript | waiting for confirmation |
| 3 | `Xác nhận gửi` | `send(confirmed=true)` | cùng transcript | sent |
| 1 | `trường bách khoa thành lập năm bao nhiêu` | `lookup` | `ui+peb1c8179815b+te69bc53ed884` | answered |
| 2 | `Ok gửi thông tin đó vào trong tele` | `send` | cùng transcript | waiting for confirmation |
| 3 | `Hủy gửi` | không gửi tiếp | cùng transcript | cancelled |

Evidence: [transcript sent](../../starter_v0/transcripts/ui_openrouter_3c130f0306e04ffbb78ac38619b6d1b9.transcript.json), [transcript cancelled](../../starter_v0/transcripts/ui_openrouter_79e77818cca744f592b527313c359f6f.transcript.json).

### B5a. Required Evidence — Tool mới, unit test, UI

| Item | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| Tool mới `dedupe` | [`tools/dedupe/`](../../starter_v0/tools/dedupe/) | dedupe theo URL/title, giữ item đầu tiên, trả metrics | input sai trả error dict, không gọi mạng |
| Unit test tool mới | [`test_tools_todo.py`](../../starter_v0/tests/test_tools_todo.py) | 3 test mới pass; combined suite 70 passed, 14 skipped | malformed item được bắt; eval model không kiểm tra output implementation |
| UI | [`app.py`](../../starter_v0/app.py), lệnh `python -m streamlit run app.py`, local `http://127.0.0.1:8501` | app khởi động và trả HTTP 200; có transcript/download/confirmation controls | chưa có public deployment; cần cấu hình API key để chat live |

### B5. Bonus Evidence

Không thực hiện các bonus Small Local Model, hơn 3 tool mới, test challenge 0 skipped hoặc Telegram evidence riêng cho bonus.

### B7. Small Local Model Challenge (bonus)

Không thực hiện.

## 5. Khó khăn và cách xử lý

- Full pytest ban đầu không collect được `test_streamlit_app.py` vì môi trường thiếu Streamlit; đã cài dependency theo `requirements.txt` để chạy UI. Bộ test CP3/contract/example chạy được với 70 passed và 14 skipped.
- Các run base/group đều dùng provider thật và không có provider error.
- Public URL chưa được deploy; bằng chứng UI hiện là local URL và transcript JSON.

## 6. Tổng hợp đóng góp

- Chi tiết đóng góp của từng thành viên nằm trong TEAM.md và các báo cáo cá nhân report/team/MSSV_HoTen.md.
## 7. Hạn chế và hướng cải thiện — B6. Reflection

- Fix thuộc `system_prompt.md`: không đoán dữ liệu thiếu, routing, no-tool boundary, xử lý dữ liệu không tin cậy và confirmation boundary.
- Fix thuộc `tools.yaml`: điều kiện dùng/không dùng, chuẩn hóa query, handle, timeframe, search type, URL và `confirmed=true`.
- Failure cần review thủ công: độ đúng của nội dung và nguồn web, chất lượng tóm tắt, policy injection và việc gửi Telegram ngoài ý muốn; routing/argument eval không chấm được các điểm này.
- Nếu có thêm một vòng: thêm test riêng cho title fallback và item không có URL/title của `dedupe`, chạy full pytest sau khi cài dependency, rồi deploy public UI.

## 8. Tài liệu tham khảo

- [README.md](../../README.md)
- [RUBRIC.md](../../RUBRIC.md)
- [System prompt](../../starter_v0/artifacts/system_prompt.md)
- [Tool declarations](../../starter_v0/artifacts/tools.yaml)
- [Base/version log](../../starter_v0/artifacts/version_log.csv)
- [Group eval](../../starter_v0/data/eval_group.json)
