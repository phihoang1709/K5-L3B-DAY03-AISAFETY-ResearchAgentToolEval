# Báo cáo cá nhân — Nguyễn Phi Hoàng — 2A202603952

## 1. Thông tin thành viên

- Họ tên: Nguyễn Phi Hoàng
- MSSV: 2A202603952
- Email:

## 2. Phần việc phụ trách

- UI Streamlit, quản lý phiên và transcript, xác nhận gửi Telegram, tích hợp.
- Phần tiếp theo theo kế hoạch: phụ trách `rank_relevance`, tích hợp ba tool bổ sung và chạy bằng chứng cuối; code hiện được Codex hỗ trợ triển khai, chưa commit.
- Còn cần: người ngoài nhóm thử câu hỏi trên link UI và xác nhận bản deploy khớp artifact cuối.

## 3. Đóng góp cụ thể

- Commit [`037d5f0`](https://github.com/phihoang1709/K5-L3B-DAY03-AISAFETY-ResearchAgentToolEval/commit/037d5f0): thêm UI chat Streamlit, quản lý lịch sử theo phiên, lưu/tải transcript và hiển thị lỗi provider/tool.
- Thêm bước xem nội dung và nút xác nhận/hủy trước khi gửi; xử lý lỗi Telegram giữ mô tả lỗi HTTP và che token trong exception; bổ sung test UI/session/regression.
- Commit này có run baseline, nhưng số đo v0–v4 là kết quả nhóm; không dùng các commit tối ưu prompt, dedupe hay code bổ sung chưa commit để nhận toàn bộ công của cá nhân.

## 4. Bằng chứng

- Source: [app.py](../../starter_v0/app.py), [ui_session.py](../../starter_v0/ui_session.py), [chat.py](../../starter_v0/chat.py), [send/tool.py](../../starter_v0/tools/send/tool.py).
- Test: [UI](../../starter_v0/tests/test_streamlit_app.py), [session](../../starter_v0/tests/test_ui_session.py), [Telegram regression](../../starter_v0/tests/test_send_errors.py). Toàn suite: 149 passed, 14 skipped, 0 failed/error.
- Bằng chứng cuối dùng cùng v4: [CLI 5 lượt](../../starter_v0/transcripts/v4_openrouter_20261110T231201448826.transcript.json), [UI 6 lượt](../../starter_v0/transcripts/v4_openrouter_47bebc6ecb21423abe67cddb790104c8.transcript.json); đây là kịch bản tự động gọi provider thật, không phải đánh giá của người dùng ngoài nhóm.
- Số liệu nhóm và giới hạn: [group_report.md](group_report.md). Link UI: [AISAFETY Streamlit](https://k5-l3b-day03-aisafety-researchagenttooleval-6ftuhztxnienlwuu6g.streamlit.app/).
- AI/công cụ: Codex hỗ trợ code, test, tổng hợp log và báo cáo; Claude Code đã được khởi chạy review qua Herdr nhưng dừng tại prompt quyền; chưa có findings. Kiểm chứng bằng pytest, đối chiếu hash/run/transcript và review độc lập; không suy diễn từ mock test thành gửi Telegram thật.

## 5. Tự đánh giá

- Chưa điền nhận xét trải nghiệm hoặc điểm tự đánh giá thay Hoàng; cần thành viên tự bổ sung sau khi đọc và giải thích được code.
- Đã có bằng chứng UI/session và regression ở commit nêu trên. Toàn suite còn 14 TODO skipped; không tuyên bố đạt 0 skipped.
- Còn thiếu nghiệm thu link UI bởi người ngoài nhóm và xác nhận deploy artifact v4. Kênh Telegram hiện public, chưa đáp ứng yêu cầu private channel; chưa làm local-model challenge.
- Việc còn lại: rà lại phân công/đóng góp cùng Hoàn, hoàn thiện thông tin chưa xác nhận và quyết định commit/push sau review.
