# Main application with histogram button
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
from PIL import Image, ImageTk

from config import CANVAS_SIZE, EXIF_TAGS
from exif_utils import read_exif, gps_to_latlon
from graph_utils import plot_frequency
from map_utils import fetch_static_map, open_interactive_map
from gpt_utils import predict_location
from histogram_utils import show_histogram
import exif_copy_utils

class Model:
    """데이터 처리 및 비즈니스 로직"""
    def __init__(self):
        self.selected_paths = []
        self.current_coords = None
        self.current_exif = None
        
    def load_single_image(self, path):
        """단일 이미지 로드하고 EXIF 데이터 추출"""
        try:
            exif, gps_raw = read_exif(path)
            coords = gps_to_latlon(gps_raw)
            self.current_exif = exif
            self.current_coords = coords
            return exif, coords
        except Exception as e:
            raise ValueError(f"이미지 로드 중 오류 발생: {e}")
    
    def save_dataframe(self, df):
        """데이터프레임을 파일로 저장"""
        ftypes = [('CSV','*.csv'), ('Excel','*.xlsx')]
        fp = filedialog.asksaveasfilename(
            defaultextension='.csv',
            filetypes=ftypes,
            initialfile='exif_data',
            title='내보내기'
        )
        if not fp:
            return False
            
        try:
            ext = os.path.splitext(fp)[1].lower()
            if ext == '.xlsx':
                df.to_excel(fp, index=False)
                return "Excel로 저장되었습니다."
            else:
                df.to_csv(fp, index=False, encoding='utf-8-sig')
                return "CSV로 저장되었습니다."
        except Exception as e:
            raise IOError(f"파일 저장 중 오류 발생: {e}")
    
    def process_multiple_images(self, paths):
        """여러 이미지 처리 및 통계 생성"""
        records = []
        freq = {'FNumber':[], 'ISOSpeedRatings':[], 'ExposureTime':[]}
        
        for fp in paths:
            try:
                exif, _ = read_exif(fp)
                fname = os.path.basename(fp)
                for t, v in exif.items():
                    records.append({'File': fname, 'Tag': t, 'Value': v})
                
                for t in freq:
                    if t in exif:
                        freq[t].append(exif[t])
            except Exception as e:
                print(f"경고: {fname} 처리 중 오류 - {e}")
                
        # 빈도 그래프 생성
        plot_frequency(freq)
        
        # 데이터프레임 생성
        df_long = pd.DataFrame(records)
        if not df_long.empty:
            df_wide = df_long.pivot(index='File', columns='Tag', values='Value').reset_index()
            # 열 순서 조정
            cols = ['File'] + [t for t in EXIF_TAGS if t in df_wide.columns]
            df_wide = df_wide[cols]
            return df_wide
        return None


class View(ttk.Frame):
    """사용자 인터페이스"""
    def __init__(self, master, controller):
        super().__init__(master, padding=10)
        self.controller = controller
        self.pack(fill='both', expand=True)
        self._build_ui()
        self._imgtk = None  # 이미지 객체 참조 유지
        
    def _build_ui(self):
        """UI 구성 요소 생성"""
        # 상단 도구 모음
        bar = ttk.Frame(self)
        bar.pack(fill='x', pady=6)
        
        ttk.Button(bar, text='사진 첨부', command=self.controller.on_attach).pack(side='left')
        
        self.btn_hist = ttk.Button(bar, text='히스토그램', state='disabled', 
                                  command=self.controller.show_hist)
        self.btn_hist.pack(side='left', padx=4)
        
        self.btn_map = ttk.Button(bar, text='지도 보기', state='disabled', 
                                 command=self.controller.show_map)
        self.btn_map.pack(side='left', padx=4)
        
        self.btn_guess = ttk.Button(bar, text='장소 추정', state='disabled', 
                                   command=self.controller.guess_location)
        self.btn_guess.pack(side='left')
        
        ttk.Button(bar, text='EXIF 복사', command=self.controller.copy_exif).pack(side='left', padx=4)
        
        # 본문 영역
        body = ttk.Frame(self)
        body.pack(fill='both', expand=True)
        
        self.canvas = tk.Canvas(body, width=CANVAS_SIZE[0], height=CANVAS_SIZE[1], 
                              bg='#fafafa', highlightthickness=1, highlightbackground='#ccc')
        self.canvas.pack(side='left', padx=(0,8))
        
        self.text = tk.Text(body, wrap='word', width=45)
        self.text.pack(side='left', fill='both', expand=True)
    
    def display_image(self, img_path):
        """이미지를 캔버스에 표시"""
        try:
            img = Image.open(img_path)
            img.thumbnail(CANVAS_SIZE)
            self._imgtk = ImageTk.PhotoImage(img)
            self.canvas.delete('all')
            self.canvas.create_image(CANVAS_SIZE[0]//2, CANVAS_SIZE[1]//2, image=self._imgtk)
            return True
        except Exception as e:
            self.clear_display()
            messagebox.showerror("이미지 표시 오류", str(e))
            return False
    
    def display_exif(self, exif, coords=None):
        """EXIF 정보를 텍스트 영역에 표시"""
        self.text.delete('1.0', 'end')
        
        for tag in EXIF_TAGS:
            if tag in exif and exif[tag]:
                self.text.insert('end', f'{tag} : {exif[tag]}\n')
        
        if coords:
            lat, lon = coords
            self.text.insert('end', f'GPS: {lat:.5f}, {lon:.5f}\n')
            self.enable_map_button()
        else:
            self.text.insert('end', 'GPS 정보 없음\n')
            self.disable_map_button()
            
        self.enable_buttons()
    
    def clear_display(self):
        """화면 초기화"""
        self.text.delete('1.0', 'end')
        self.canvas.delete('all')
        self.disable_all_buttons()
    
    def enable_buttons(self):
        """기능 버튼 활성화"""
        self.btn_hist.state(['!disabled'])
        self.btn_guess.state(['!disabled'])
    
    def enable_map_button(self):
        """지도 버튼 활성화"""
        self.btn_map.state(['!disabled'])
    
    def disable_map_button(self):
        """지도 버튼 비활성화"""
        self.btn_map.state(['disabled'])
    
    def disable_all_buttons(self):
        """모든 기능 버튼 비활성화"""
        self.btn_map.state(['disabled'])
        self.btn_guess.state(['disabled'])
        self.btn_hist.state(['disabled'])


class Controller:
    """컨트롤러 - 사용자 입력 처리 및 모델과 뷰 연결"""
    def __init__(self, root):
        self.root = root
        self.model = Model()
        self.view = View(root, self)
    
    def on_attach(self):
        """이미지 첨부 처리"""
        paths = filedialog.askopenfilenames(
            filetypes=[('Images', '*.jpg *.jpeg *.png *.tif *.tiff')]
        )
        if not paths:
            return
            
        self.model.selected_paths = list(paths)
        
        if len(self.model.selected_paths) == 1:
            self.handle_single(self.model.selected_paths[0])
        else:
            self.handle_multi(self.model.selected_paths)
    
    def handle_single(self, path):
        """단일 이미지 처리"""
        try:
            # 이미지 표시
            if not self.view.display_image(path):
                return
                
            # EXIF 데이터 추출 및 표시
            exif, coords = self.model.load_single_image(path)
            self.view.display_exif(exif, coords)
        except Exception as e:
            self.view.clear_display()
            messagebox.showerror("오류", str(e))
    
    def handle_multi(self, paths):
        """다중 이미지 처리"""
        try:
            df = self.model.process_multiple_images(paths)
            if df is not None:
                try:
                    result = self.model.save_dataframe(df)
                    if result:
                        messagebox.showinfo('완료', result)
                except IOError as e:
                    messagebox.showerror('저장 오류', str(e))
            else:
                messagebox.showinfo('정보', '처리할 EXIF 데이터가 없습니다.')
        except Exception as e:
            messagebox.showerror('처리 오류', str(e))
        finally:
            self.view.clear_display()
    
    def show_hist(self):
        """히스토그램 표시"""
        if not self.model.selected_paths:
            return
        try:
            show_histogram(self.model.selected_paths[0])
        except Exception as e:
            messagebox.showerror('히스토그램 오류', str(e))
    
    def show_map(self):
        """지도 표시"""
        if not self.model.current_coords:
            messagebox.showinfo('정보', 'GPS 정보가 없습니다.')
            return
            
        lat, lon = self.model.current_coords
        try:
            img = fetch_static_map(lat, lon)
            top = tk.Toplevel(self.root)
            top.title('지도 보기')
            photo = ImageTk.PhotoImage(img)
            tk.Label(top, image=photo).pack()
            top.image = photo  # 참조 유지
        except Exception:
            try:
                open_interactive_map(lat, lon)
            except Exception as e:
                messagebox.showerror('지도 오류', f'지도를 표시할 수 없습니다: {e}')
    
    def guess_location(self):
        """위치 추정"""
        if not self.model.selected_paths:
            return
            
        try:
            res = predict_location(self.model.selected_paths[0])
            messagebox.showinfo('GPT-4o 추정 결과', res or '추정 불가')
        except Exception as e:
            messagebox.showerror('추정 오류', str(e))
    
    def copy_exif(self):
        """EXIF 복사"""
        src = filedialog.askopenfilename(
            title='EXIF 복사 - 원본 선택',
            filetypes=[('Images', '*.jpg *.jpeg *.png *.tif *.tiff')]
        )
        if not src:
            return
            
        tgt = filedialog.askopenfilename(
            title='EXIF 복사 - 대상 선택',
            filetypes=[('Images', '*.jpg *.jpeg *.png *.tif *.tiff')]
        )
        if not tgt:
            return
            
        try:
            exif_copy_utils.copy_exif(src, tgt)
            messagebox.showinfo('완료', f'EXIF metadata를 {tgt}에 복사했습니다.')
        except Exception as e:
            messagebox.showerror('오류', f'EXIF 복사 실패: {e}')


def main():
    """메인 애플리케이션 실행"""
    root = tk.Tk()
    root.title('주.사.위 EXIF Viewer')
    root.geometry('800x520')
    
    # 스타일 설정
    style = ttk.Style()
    style.configure('TButton', font=('맑은 고딕', 9))
    style.configure('TFrame', background='#f0f0f0')
    
    app = Controller(root)
    root.mainloop()


if __name__ == '__main__':
    main()
