# BTL2: Game Playing Agent - Chess AI (Nhập môn Trí tuệ Nhân tạo)

## Giới thiệu

Đây là project Bài tập lớn 2 môn Nhập môn Trí tuệ Nhân tạo (HK2 2024-2025). Mục tiêu là xây dựng một agent chơi Cờ Vua sử dụng thuật toán Minimax với các kỹ thuật tối ưu hóa như Alpha-Beta Pruning, Iterative Deepening, Transposition Tables, và Quiescence Search. Agent được thiết kế để chơi đúng luật, có khả năng đánh bại agent ngẫu nhiên và cung cấp các cấp độ khó khác nhau. Project không sử dụng Machine Learning.

## Thành viên Nhóm

*   Phan Đình Tuấn Anh - 2210118
*   Hồ Anh Dũng - 2310543
*   Nguyễn Trọng Tài - 2212995
*   Nguyễn Thiện Minh - 2312097

## Yêu cầu Hệ thống

*   Các thư viện được liệt kê trong `requirements.txt`

## Cài đặt

1.  **Clone Repository:**
    ```bash
    git clone https://github.com/minhnguyenrun/Pychess
    cd Pychess
    ```
2.  **Cài đặt thư viện:** (Nên sử dụng môi trường ảo - virtual environment)
    ```bash
    pip install -r requirements.txt
    ```


## Cách Chạy

Chạy file `main.py` từ terminal:

```bash
python main.py
```

Chương trình sẽ hiển thị menu chính để lựa chọn chế độ chơi:

*   **Player vs Player:** Hai người chơi trên cùng máy.
*   **Player vs AI:** Người chơi đấu với AI. Bạn sẽ được chọn độ khó (Easy/Medium/Hard) và màu quân (Trắng/Đen).
*   **AI vs Random:** AI đấu với một agent chơi ngẫu nhiên. Bạn sẽ được chọn độ khó cho AI và màu quân AI sẽ chơi.
*   **Exit:** Thoát chương trình.

**Chạy chế độ đánh giá hiệu năng (tùy chọn):**

*   Đánh giá hiệu năng cơ bản (thời gian, số nút duyệt) ở các độ sâu:
    ```bash
    python main.py --evaluate [depths] [moves_per_depth]
    # Ví dụ: python main.py --evaluate 2,3,4 10
    ```
*   Đánh giá AI đấu với Random Agent nhiều ván:
    ```bash
    python main.py --eval-random [ai_depth] [num_games]
    # Ví dụ: python main.py --eval-random 3 20
    ```

## Cấu trúc File

*   `main.py`: Điểm bắt đầu, quản lý luồng chính, menu, xử lý sự kiện.
*   `game_state.py`: Engine Cờ Vua, quản lý trạng thái, luật chơi, sinh nước đi.
*   `minimax_ai.py`: Logic AI, thuật toán Minimax/Alpha-Beta, hàm lượng giá.
*   `chess_visualizer.py`: Hiển thị giao diện đồ họa (GUI) bằng Pygame.
*   `requirements.txt`: Danh sách các thư viện Python cần thiết.
*   `README.md`: File hướng dẫn này.
*   `images/`: Thư mục chứa hình ảnh các quân cờ (cần được cung cấp).
*   `Image/`: Thư mục chứa các hình ảnh/biểu đồ dùng trong báo cáo/slide 

## Video Báo Cáo và Demo

*   **Video báo cáo giải thích thuật toán:** [Xem video trên YouTube](https://www.youtube.com/watch?v=vu7UjjQ77S0)
*   **Chess AI đấu với bot 1850 Elo:** [Xem video demo](https://www.youtube.com/watch?v=huqCbpy91o4)

## Đánh Giá Hiệu Năng

Agent có thể:
*   Chiến thắng Random Agent trong tất cả các trận
*   Chơi có tính cạnh tranh với bot cờ vua mức 1850 Elo


## Lưu ý

*   Project này tập trung vào thuật toán tìm kiếm, hàm lượng giá có thể chưa tối ưu hoàn hảo cho mọi tình huống phức tạp.

