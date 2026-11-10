# Báo cáo cá nhân — Nguyễn Công Hoàn

## 1. Thông tin thành viên

- Họ tên: Nguyễn Công Hoàn
- MSSV: 2A202603972
- Email: 26ai.hoannc@vinuni.edu.vn


## 2. Phần việc phụ trách

 **CP3/CP4: thêm tool mới, viết unit test offline và xây dựng group eval** cho Research Agent.

## 3. Đóng góp cụ thể

- Thiết kế và triển khai tool local `dedupe` trong `starter_v0/tools/dedupe/`.
- Định nghĩa hành vi dedupe theo URL chuẩn hóa hoặc title chuẩn hóa, giữ item xuất hiện đầu tiên và giữ nguyên thứ tự.
- Thêm `TOOL.md` với frontmatter đúng contract của project.
- Đăng ký tool `dedupe` trong `starter_v0/tools/__init__.py` và khai báo trong `starter_v0/artifacts/tools.yaml`.
- Viết 3 unit test cho tool mới:
  - happy path với các URL trùng;
  - input không phải list;
  - item malformed trả error dict thay vì raise exception.
- Viết 10 case trong `starter_v0/data/eval_group.json`, gồm 5 single-turn và 5 multi-turn; trong đó G05 kiểm tra model route tới `dedupe`.
- Chạy group eval bằng OpenRouter và kiểm tra routing, arguments, multi-turn và provider error.
- Cập nhật checklist CP3/CP4 và bổ sung evidence vào group report.

## 4. Bằng chứng

- Tool implementation: [`starter_v0/tools/dedupe/tool.py`](../../starter_v0/tools/dedupe/tool.py)
- Tool contract: [`starter_v0/tools/dedupe/TOOL.md`](../../starter_v0/tools/dedupe/TOOL.md)
- Registry: [`starter_v0/tools/__init__.py`](../../starter_v0/tools/__init__.py)
- Declaration: [`starter_v0/artifacts/tools.yaml`](../../starter_v0/artifacts/tools.yaml)
- Unit tests: [`starter_v0/tests/test_tools_todo.py`](../../starter_v0/tests/test_tools_todo.py)
- Group eval cases: [`starter_v0/data/eval_group.json`](../../starter_v0/data/eval_group.json)
- Group eval run: [`v3_B_group_openrouter_20261110T221819343346.json`](../../starter_v0/runs/v3_B_group_openrouter_20261110T221819343346.json)
- Group eval kết quả: 10/10 case pass, 0 provider error, routing accuracy 1.0, argument accuracy 1.0, multi-turn accuracy 1.0.
- Unit/contract/example test: `70 passed, 14 skipped`; 3 test của `dedupe` đều pass.
- Commit triển khai: `edd3fa5` — `feat: add dedupe tool and group evals`.

AI/công cụ được dùng để hỗ trợ đọc contract, kiểm tra schema và rà soát test. Kết quả được tự kiểm tra bằng pytest, JSON schema checks, tool contract test và provider eval thực tế; không dựa chỉ vào nội dung do AI sinh ra.

## 5. Tự đánh giá

Phần CP3/CP4 đã hoàn thành đúng yêu cầu: tool mới có implementation, declaration, registry, tài liệu và unit test; group eval có đủ 10 case theo tỷ lệ 5 single-turn/5 multi-turn và chạy đạt 10/10.


