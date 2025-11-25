import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os

# 設定切片大小
TILE_WIDTH = 16
TILE_HEIGHT = 16

class TileSelectorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Tile Selector to C# Array")
        self.root.geometry("1000x700")

        # 狀態變數
        self.image_path = None
        self.original_image = None
        self.tiles_data = []  # 儲存每個格子的資訊
        self.selected_indices = set() # 儲存被選中的格子 index
        self.tk_image = None
        self.scale_factor = 2.0 # 預覽時放大倍率
        
        # 拖曳相關狀態
        self.is_dragging_mode_add = True 
        self.last_processed_index = -1 

        # --- UI 佈局 ---
        
        # 頂部控制列
        control_frame = tk.Frame(root, pady=10)
        control_frame.pack(fill=tk.X)

        btn_load = tk.Button(control_frame, text="1. 載入圖片", command=self.load_image, bg="#e1f5fe")
        btn_load.pack(side=tk.LEFT, padx=10)
        
        # 新增：全不選功能
        btn_clear = tk.Button(control_frame, text="重置/全不選", command=self.clear_selection, bg="#ffcdd2")
        btn_clear.pack(side=tk.LEFT, padx=10)

        btn_save = tk.Button(control_frame, text="2. 匯出 C# 陣列", command=self.save_data_csharp, bg="#c8e6c9")
        btn_save.pack(side=tk.LEFT, padx=10)
        
        self.lbl_status = tk.Label(control_frame, text="請載入一張圖片...", fg="gray")
        self.lbl_status.pack(side=tk.LEFT, padx=10)

        # 主要畫布區域 (含捲軸)
        canvas_frame = tk.Frame(root)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(canvas_frame, bg="#333333")
        
        v_scroll = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        h_scroll = tk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        
        self.canvas.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas.bind("<Button-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)

    def is_tile_empty(self, img_crop):
        if img_crop.mode != 'RGBA':
            img_crop = img_crop.convert('RGBA')
        alpha = img_crop.split()[-1]
        return alpha.getextrema()[1] == 0

    def load_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp")])
        if not file_path:
            return

        self.image_path = file_path
        self.original_image = Image.open(file_path).convert("RGBA")
        
        self.tiles_data = []
        self.selected_indices = set()
        self.process_image()
        self.draw_canvas()
        self.lbl_status.config(text=f"已載入: {os.path.basename(file_path)} | ID 從 0 開始")

    def process_image(self):
        width, height = self.original_image.size
        rows = height // TILE_HEIGHT
        cols = width // TILE_WIDTH
        
        current_id = 0 
        
        for r in range(rows):
            for c in range(cols):
                x = c * TILE_WIDTH
                y = r * TILE_HEIGHT
                box = (x, y, x + TILE_WIDTH, y + TILE_HEIGHT)
                tile_img = self.original_image.crop(box)
                
                is_empty = self.is_tile_empty(tile_img)
                
                tile_info = {
                    "index": len(self.tiles_data),
                    "row": r,
                    "col": c,
                    "x": x,
                    "y": y,
                    "is_empty": is_empty,
                    "id": current_id if not is_empty else None
                }
                
                if not is_empty:
                    current_id += 1
                    
                self.tiles_data.append(tile_info)

    def draw_canvas(self):
        self.canvas.delete("all")
        
        display_w = int(self.original_image.width * self.scale_factor)
        display_h = int(self.original_image.height * self.scale_factor)
        
        resized_img = self.original_image.resize((display_w, display_h), Image.NEAREST)
        self.tk_image = ImageTk.PhotoImage(resized_img)
        
        self.canvas.create_image(0, 0, image=self.tk_image, anchor=tk.NW)
        self.canvas.config(scrollregion=(0, 0, display_w, display_h))
        
        for tile in self.tiles_data:
            x1 = tile["x"] * self.scale_factor
            y1 = tile["y"] * self.scale_factor
            x2 = x1 + (TILE_WIDTH * self.scale_factor)
            y2 = y1 + (TILE_HEIGHT * self.scale_factor)
            
            if tile["is_empty"]:
                self.canvas.create_rectangle(x1, y1, x2, y2, fill="#000000", stipple="gray50", outline="")
            else:
                self.canvas.create_rectangle(x1, y1, x2, y2, outline="#555555", width=1, tags=f"tile_{tile['index']}")
                self.canvas.create_text(x1 + 2, y1 + 2, text=str(tile["id"]), anchor=tk.NW, fill="yellow", font=("Arial", 8, "bold"))

    def get_tile_index_at_mouse(self, event):
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        col = int(canvas_x // (TILE_WIDTH * self.scale_factor))
        row = int(canvas_y // (TILE_HEIGHT * self.scale_factor))
        
        for tile in self.tiles_data:
            if tile["row"] == row and tile["col"] == col:
                return tile["index"]
        return -1

    def update_tile_selection(self, idx, select=True):
        tile = self.tiles_data[idx]
        if tile["is_empty"]:
            return

        if select:
            self.selected_indices.add(idx)
            self.canvas.itemconfigure(f"tile_{idx}", outline="red", width=2)
        else:
            if idx in self.selected_indices:
                self.selected_indices.remove(idx)
            self.canvas.itemconfigure(f"tile_{idx}", outline="#555555", width=1)

    # --- 新增功能：清除全選 ---
    def clear_selection(self):
        # 遍歷目前已選取的索引，將其 UI 還原
        for idx in list(self.selected_indices):
            self.canvas.itemconfigure(f"tile_{idx}", outline="#555555", width=1)
        self.selected_indices.clear()

    def on_mouse_down(self, event):
        if not self.original_image: return
        idx = self.get_tile_index_at_mouse(event)
        if idx == -1: return
            
        self.last_processed_index = idx
        if idx in self.selected_indices:
            self.is_dragging_mode_add = False
            self.update_tile_selection(idx, select=False)
        else:
            self.is_dragging_mode_add = True
            self.update_tile_selection(idx, select=True)

    def on_mouse_drag(self, event):
        if not self.original_image: return
        idx = self.get_tile_index_at_mouse(event)
        if idx == -1 or idx == self.last_processed_index: return
        self.last_processed_index = idx
        self.update_tile_selection(idx, select=self.is_dragging_mode_add)

    # --- 修改功能：匯出 C# 陣列 ---
    def save_data_csharp(self):
        if not self.tiles_data or not self.selected_indices:
            messagebox.showwarning("警告", "請先選擇至少一個格子")
            return
            
        save_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text file", "*.txt"), ("C# file", "*.cs")])
        if not save_path:
            return
            
        # 1. 找出最小包圍矩形 (Bounding Box)
        # 取得所有被選取格子的 row 和 col
        selected_tiles = [self.tiles_data[i] for i in self.selected_indices]
        
        rows = [t["row"] for t in selected_tiles]
        cols = [t["col"] for t in selected_tiles]
        
        min_row, max_row = min(rows), max(rows)
        min_col, max_col = min(cols), max(cols)
        
        # 2. 計算矩陣大小
        height = max_row - min_row + 1
        width = max_col - min_col + 1
        
        # 3. 建立並初始化二維陣列 (預設填入 -1)
        # matrix[row][col]
        matrix = [[-1 for _ in range(width)] for _ in range(height)]
        
        # 4. 填入選取資料 (平移座標：減去 min_row 和 min_col)
        for tile in selected_tiles:
            rel_r = tile["row"] - min_row
            rel_c = tile["col"] - min_col
            matrix[rel_r][rel_c] = tile["id"]
            
        # 5. 格式化為 C# 字串
        # 格式: int[rows,cols] item = { ... }
        
        lines = []
        for r_idx in range(height):
            # 將 list 轉為字串，例如: "0, 1, -1, 5"
            row_content = ", ".join(map(str, matrix[r_idx]))
            lines.append(f"    {{{row_content}}}")
            
        joined_lines = ",\n".join(lines)
        
        # 組合最終字串
        csharp_code = f"private int[,] item = {{\n{joined_lines}\n}};"
        
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(csharp_code)
            
            messagebox.showinfo("成功", f"C# 陣列已儲存至:\n{save_path}\n矩陣大小: {height}x{width}")
        except Exception as e:
            messagebox.showerror("錯誤", f"儲存失敗: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = TileSelectorApp(root)
    root.mainloop()