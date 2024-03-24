from tracemalloc import start
from utilities import try_add
from ModLoader import ModContentPack, generate_mod_dict, load_mod, load_mod, get_modloadorder, ModLoadFolder, load_mod_single, load_xmls
import TranslationExtractor as PE
from tkinter import *
from tkinter.ttk import *
from tkinter import filedialog, messagebox
import lxml.etree as ET
from fileparser import BFS, listdir_abspath
import os

class TranslationFileRenamer(Frame):
    def __init__(self, Tab: Widget):
        self.parent = Tab
        self.parent.rowconfigure(0, weight=1)
        self.parent.columnconfigure(0, weight=1)
        self.frame = Frame(Tab, style="Red.TFrame")
        self.frame.grid(row=0, column=0, sticky="nswe")
        self.leftframe = Frame(self.frame, style="Green.TFrame")
        self.middleframe = Frame(self.frame, style="Blue.TFrame")
        self.rightframe = Frame(self.frame, style="Yellow.TFrame")
        self.frame.columnconfigure(0, weight=9)
        self.frame.rowconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=2)
        self.frame.columnconfigure(2, weight=9)
        self.leftframe.grid(row=0, column=0, sticky="nswe")
        self.middleframe.grid(row=0, column=1, sticky="nswe")
        self.rightframe.grid(row=0, column=2, sticky="nswe")

    def preview(self, *args):

        pass


class Patch_Extract_Tab(Frame):
    _singleton = None

    def __new__(cls, Tab: Widget):
        if Patch_Extract_Tab._singleton is None:
            Patch_Extract_Tab._singleton = super(Patch_Extract_Tab, cls).__new__(cls)
        return Patch_Extract_Tab._singleton

    def __init__(self, Tab: Widget):
        super().__init__(Tab)
        self.cur_state = "SelectDir"
        self.dirs: list[str] = []
        self.dirCheckButtons: list[Checkbutton] = []
        self.dirSelected: list[BooleanVar] = []
        self.Tab = Tab
        self.ext_dir = StringVar(self.Tab, name="ext_dir1")
        self.ext_dir.trace_add("write", self.update)
        # 用于让Entry不那么频繁触发ext_dir的trace的变量
        self.ext_dir_wrap = StringVar(self.Tab, name="ext_dir_wrap")
        self.Title = Frame(Tab, height=100, style="white.TFrame")
        self.Title.grid(row=0, sticky="nswe", columnspan=2)
        self.Title.grid_rowconfigure(0, weight=1)
        self.Title.grid_columnconfigure(0, weight=1)
        self.Title.grid_columnconfigure(1, weight=9)
        self.Draw_Title(self.Title)
        self.Tab.grid_columnconfigure(0, weight=1)
        self.Tab.grid_rowconfigure(0, minsize=50)
        self.Main_Rect = Frame(Tab, style="Green.TFrame")
        self.Main_Rect.grid(row=1, column=0, sticky="nswe")
        self.Main_Rect.grid_rowconfigure(0, weight=1)
        self.Main_Rect.grid_columnconfigure(0, weight=1)
        self.Draw_Main(self.Main_Rect)
        self.Frame_Config = Frame(Tab, style="yellow.TFrame", width=100)
        self.Frame_Config.grid(row=1, column=1, sticky="nswe")
        self.Draw_Config(self.Frame_Config)
        self.Bottom_Buttons = Frame(
            Tab, width=Tab.winfo_reqwidth(), height=20, style="Blue.TFrame"
        )
        self.Bottom_Buttons.grid(row=2, sticky="nswe", columnspan=2)
        self.Draw_Bottom(self.Bottom_Buttons)
        self.Tab.rowconfigure(0, minsize=40, pad=10)
        self.Tab.rowconfigure(1, weight=1)
        self.Tab.rowconfigure(2, minsize=40, pad=10)
        self.Tab.columnconfigure(1, weight=1, minsize=150)
        self.Tab.columnconfigure(0, weight=9)
        """ self.entry = Entry(Tab)
        def execute(event):
            command = self.entry.get()
            print(eval(command))
        self.entry.bind("<Return>", execute)
        self.entry.grid(row=2, column=1, sticky='we') """
        self.Title.bind_all("<ButtonPress-1>", self.check_direntry)
        self.ver_bools = None
        self.update()

    def update(self, *args):
        # print(args)
        if not self.ext_dir.get():
            return
        max_width = 0
        self.ext_dir_wrap.set(self.ext_dir.get())
        # self.canvas.grid_forget()
        self.dirs.clear()
        self.dirSelected.clear()
        for button in self.dirCheckButtons:
            button.destroy()
        self.canvas.delete("all")
        self.Checkboxes = Frame(self.canvas)
        row = 1
        self.dirs.extend(
            [
                f"{self.ext_dir.get()}/{f}"
                for f in os.listdir(self.ext_dir.get())
                if os.path.isdir(f"{self.ext_dir.get()}/{f}")
                and not (f[0] == "." or f[0] == "_")
            ]
        )
        self.dirSelected.extend(
            [BooleanVar(self.Tab, False) for i in range(len(self.dirs))]
        )
        for i in range(len(self.dirs)):
            button = Checkbutton(
                self.Checkboxes,
                text=self.dirs[i],
                variable=self.dirSelected[i],
                name=f"dir{i}",
                command=self.check_checkbox,
            )
            button.grid(row=i + row, column=0, sticky="we")
            button.update_idletasks()
            max_width = max(max_width, button.winfo_width())
            # print(button.winfo_reqwidth())
            self.dirCheckButtons.append(button)
            row += 1
        # update must be placed before actually drawing (e.g. with grid or pack) the widgets
        # I'm still confused by how this actually works
        # 就算直接调整Main_Rect的大小也无济于事，在update_idletasks之后甚至还因为propagate变宽了
        # 感觉要在点击按钮之后直接在self.Tab里调整才行……
        self.canvas.update_idletasks()
        self.canvas.create_window(
            (0, 0), window=self.Checkboxes, anchor="nw", tags="MainFrame"
        )
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.canvas.grid(sticky="nswe")
        # print(self.canvas.bbox('all')[3])
        # print(self.Main_Rect.winfo_height())
        if self.canvas.bbox("all")[2] > self.Main_Rect.winfo_width() + 20:
            self.scrbrX.grid(row=1, column=0, sticky="we")
        else:
            self.scrbrX.grid_forget()
        if self.canvas.bbox("all")[3] > self.Main_Rect.winfo_height():
            self.canvas.bind_all("<MouseWheel>", self.on_mousewheel)
            self.scrbrY.grid(row=0, column=1, sticky="ns")
        else:
            self.canvas.unbind_all("<MouseWheel>")
            self.scrbrY.grid_forget()
        """ self.Draw_Title(self.Title)
        self.Draw_Main(self.Main_Rect)
        self.Draw_Config(self.Frame_Config)
        self.Draw_Bottom(self.Bottom_Buttons) """
        super().update()

    def Draw_Title(self, outRect: Widget, **kwargs) -> None:
        Button(
            self.Title,
            text="Choose directory",
            command=lambda: (
                self.ext_dir.set(
                    filedialog.askdirectory(mustexist=True, title="选择目标文件夹")
                )
            ),
        ).grid(row=0, column=0, sticky="we")
        self.Entry = Entry(self.Title, textvariable=self.ext_dir_wrap)
        self.Entry.grid(row=0, column=1, sticky="we")
        # 还是这个方便
        self.Entry.bind("<Return>", self.update_dir)
        self.Entry.bind("<FocusOut>", self.update_dir)

    def Draw_Main(self, outRect: Widget, **kwargs) -> None:
        self.canvas = Canvas(self.Main_Rect)
        self.scrbrY = Scrollbar(
            self.Main_Rect, orient=VERTICAL, command=self.canvas.yview
        )
        self.scrbrX = Scrollbar(
            self.Main_Rect, orient=HORIZONTAL, command=self.canvas.xview
        )
        self.canvas.configure(
            xscrollcommand=self.scrbrX.set,
            yscrollcommand=self.scrbrY.set,
            scrollregion=self.canvas.bbox("all"),
        )

    
    def Draw_Config(self, outRect: Widget, **kwargs) -> None:
        self.recursive = BooleanVar(self.Tab, True)
        self.split = BooleanVar(self.Tab, True)
        self.append = BooleanVar(self.Tab, False)
        self.resolve = BooleanVar(self.Tab, False)
        self.Defs = BooleanVar(self.Tab, True)
        self.Patches = BooleanVar(self.Tab, False)
        self.all_versions = BooleanVar(self.Tab, True)
        outRect.rowconfigure(0, weight=1)
        outRect.rowconfigure(1, weight=9)
        outRect.columnconfigure(0, weight=1)
        self.TargetGrid = Labelframe(outRect, text="Configs")
        self.TargetGrid.rowconfigure(0, weight=1)
        self.TargetGrid.columnconfigure(0, weight=1)
        self.TargetGrid.grid(row=0, column=0, sticky="nswe")
        configRect = Frame(self.TargetGrid)
        configRect.columnconfigure(0, weight=1)
        configRect.grid(row=0, column=0, sticky="nswe")
        cur_row = 0
        self.Buttons = [
            Checkbutton(configRect, text="Recursive", variable=self.recursive),
            Label(configRect, text="递归查找"),
            Checkbutton(configRect, text="Split", variable=self.split),
            Label(configRect, text="按文件分割"),
            Checkbutton(configRect, text="Append", variable=self.append),
            Label(configRect, text="追加Mod文件夹名"),
            Checkbutton(configRect, text="Resolve Inheritance", variable=self.resolve, state='disabled'),
            Label(configRect, text="处理XML继承(WIP)"),
            Checkbutton(configRect, text="Def", variable=self.Defs),
            Label(configRect, text="提取Defs"),
            Checkbutton(configRect, text="Patch", variable=self.Patches),
            Label(configRect, text="提取Patch"),
            Checkbutton(configRect, text="All versions", variable=self.all_versions, state='disabled', command=lambda : 
                        (self.update_verconfig(self.versionRect))),
            Label(configRect, text="提取所有版本(WIP)"),
        ]
        self.append_option = self.Buttons[4]
        for i in range(0, len(self.Buttons), 2):
            self.Buttons[i].grid(row=cur_row, column=0, sticky="w")
            self.Buttons[i + 1].grid(row=cur_row, column=1, sticky="w")
            cur_row += 1
        Separator(configRect, orient=HORIZONTAL).grid(
            row=cur_row, column=0, sticky="we", columnspan=2
        )
        self.versionRect = Frame(outRect, style="Red.TFrame")
        self.versionRect.columnconfigure(0, weight=1)
        self.versionRect.grid(row=1, column=0, sticky="nswe")
        self.versionRect.grid_remove()
        self.split.trace_add(
            "write",
            lambda a, b, c: (
                self.append_option.config(state="normal")
                if self.split.get()
                else (
                    self.append_option.config(state="disabled"),
                    self.append.set(False),
                )
            ),
        )

    def update_verconfig(self, outRect) -> None:
        if self.all_versions.get():
            self.versionRect.grid_remove()
            return
        self.versionRect.grid()
        versions = self.get_versions()
        if len(versions) == 0:
            return
        cur_row = 0
        self.ver_bools = [BooleanVar(outRect, False) for ver in versions]
        for ver in versions:
            Checkbutton(
                outRect, text=ver, variable=self.ver_bools[cur_row]
            ).grid(row=cur_row, column=0, sticky="w")
            cur_row += 1

    def Draw_Bottom(self, outRect: Widget, **kwargs) -> None:
        self.ExportButton = Button(
            outRect,
            text="Output Selected",
            command=self.do_extract,
            name="output",
            state="disabled",
        )
        self.ExportButton.place(relx=0.5, rely=0.5, anchor=CENTER)
        pass

    def do_extract(self) -> None:
        """
        Ver 0.1
        """
        dirs = (dirname for i, dirname in enumerate(self.dirs) if self.dirSelected[i].get())
        targets = set()
        if self.Defs.get(): targets.add('Def')
        if self.Patches.get(): targets.add('Patch')
        recursive = self.recursive.get()
        split = self.split.get()
        append = self.append.get()
        language = "ChineseSimplified"
        Total_dir = filedialog.askdirectory(mustexist=True, title="保存到……")
        for dir in dirs:
            mod_name = os.path.basename(dir)
            output_dir = f"{Total_dir}/{mod_name}/Languages/{language}/DefInjected"
            os.makedirs(output_dir, exist_ok=True)
            files = []
            for file in (BFS(dir, ["xml"]) if recursive else listdir_abspath(dir, ["xml"])):
                try:
                    root = ET.parse(file).getroot()
                    if not(root.tag == "Defs" or root.tag == "Patch"):
                        continue
                    files.append(file)
                except:
                    continue
            if split:
                for file in files:
                    try:
                        KVpair = PE.extract([file], targets)
                        for defType, KVpair in KVpair.items():
                            elemroot: ET._Element = ET.Element("LanguageData")
                            elemroot.addprevious(
                                ET.Comment("This file was generated by Patch_Extract.py")
                            )
                            tree: ET._ElementTree = ET.ElementTree(elemroot)
                            file_name = (
                                (f"{mod_name}_" if append else "") +
                                os.path.basename(file).split(".")[0] + ".xml"
                            )
                            os.makedirs(os.path.join(output_dir, defType, 'Defs'), exist_ok=True)
                            os.makedirs(os.path.join(output_dir, defType, 'Patches'), exist_ok=True)
                            for key, value in KVpair.items():
                                if value == "" or value is None: continue
                                defName = ET.SubElement(elemroot, key)
                                defName.addprevious(ET.Comment("EN: " + value.replace('--', '- -').removesuffix('-'))) # Add original text as comment
                                defName.text = value
                            #print(f"{output_dir}/{defType}/{file_name}")
                            
                            if 'Defs' in file:
                                output_path = f"{output_dir}/{defType}/Defs/{file_name}"
                            elif 'Patches' in file:
                                output_path = f"{output_dir}/{defType}/Patches/{file_name}"
                            else:
                                output_path = f"{output_dir}/{defType}/{file_name}"
                            tree.write(
                                output_path,
                                pretty_print=True,
                                xml_declaration=True,
                                encoding="utf-8"
                        )
                    except Exception as e:
                        print(f"Error when parsing file {file} : {e}")
            else:
                results = PE.extract(files, targets)
                for defType, KVpair in results.items():
                    os.makedirs(os.path.join(output_dir, defType), exist_ok=True)
                    elemroot: ET._Element = ET.Element("LanguageData")
                    elemroot.addprevious(
                        ET.Comment("This file was generated by Patch_Extract.py")
                    )
                    etree: ET._ElementTree = ET.ElementTree(elemroot)
                    for key, value in KVpair.items():
                        if value == "" or value is None: continue
                        defName = ET.SubElement(elemroot, key)
                        defName.addprevious(ET.Comment("EN: " + value.replace('--', '- -').removesuffix('-'))) # XML comments cannot contain '--' or end with '-'
                        defName.text = value
                    output_path = f"{output_dir}/{defType}/Extracted.xml"
                    self.infoText.insert(END, f"Writing to {output_path}\n")
                    etree.write(output_path, pretty_print=True, xml_declaration=True, encoding='utf-8')
        messagebox.showinfo("Done", "Extraction complete!")
    def check_direntry(self, *args) -> None:
        if (
            self.winfo_containing(self.winfo_pointerx(), self.winfo_pointery())
            != self.Entry
        ):
            self.Tab.focus_set()

    def check_checkbox(self) -> None:
        if any(f.get() for f in self.dirSelected):
            self.ExportButton.config(state="normal")
        else:
            self.ExportButton.config(state="disabled")

    def update_dir(self, *args) -> None:
        self.ext_dir.set(self.ext_dir_wrap.get())

    def on_mousewheel(self, event) -> None:
        self.canvas.yview_scroll(-1 * (event.delta // 120), "units")

    def get_versions(self) -> set[str]:
        dirs = (
            dirname for i, dirname in enumerate(self.dirs) if self.dirSelected[i].get()
        )
        versions: set[str] = set()
        for dir in dirs:
            versions.update(ModLoadFolder(dir).allSupportedVersions())
        return versions

    @staticmethod
    def checkbtn_label_pair(outRect: Frame, **kwargs: tuple[Variable, str]) -> list[tuple[Checkbutton, Label]]:
        """
        :param kwargs: the key is Checkbutton.text, value is tuple(Checkbutton.variable, Label.text)
        """
        if len(kwargs.keys()) % 2 != 0:
            raise ValueError("Arguments must be in pairs")
        pairs: tuple[Checkbutton, Label] = []
        for item in kwargs.items():
            if not isinstance(item[1][0], BooleanVar):
                raise ValueError("First element of each pair must be a BooleanVar")
            pairs.append(
                (
                    Checkbutton(outRect, text=item[0], variable=item[1][0]),
                    Label(outRect, text=item[1][1])
                )
            )
        return pairs



class MainWindow(Tk):
    def __init__(self) -> None:
        super().__init__()
        Style().configure("Red.TFrame", background="red")
        Style().configure("Blue.TFrame", background="blue")
        Style().configure("Green.TFrame", background="green")
        Style().configure("Yellow.TFrame", background="yellow")
        Style().configure("White.TFrame", background="white")
        self.title("RimTrans_PY")
        self.geometry("800x600")
        self.resizable(False, False)
        self.notebook = Notebook(self, width=800, height=600)
        self.Translation_Clean = Frame(self.notebook)
        self.Test = Frame(self.notebook, style="Red.TFrame", width=800, height=600)
        self.Test.grid()
        self.Test_Tab = Patch_Extract_Tab(self.Test)
        self.Translation_Rename = Frame(
            self.notebook, style="Green.TFrame", width=800, height=600
        )
        self.Translation_Rename_Tab = TranslationFileRenamer(self.Translation_Rename)
        self.notebook.add(self.Test, text="Patch Extractor")
        #self.notebook.add(self.Translation_Rename, text="Translation Renamer")
        self.notebook.pack()


def main() -> None:
    app = MainWindow()
    Style(app).theme_use("vista")
    app.mainloop()