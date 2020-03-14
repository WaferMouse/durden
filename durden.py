import tkinter as tk
import tkinter.ttk as ttk
import tkinter.filedialog
import array
import copy

# width = self.plane_map_width.get() tiles (10 * 4)
# height = self.plane_map_height.get() tiles (7 * 4)

# paletteline colour tile 

# map editor needs tile paletteline
# tile editor needs tile paletteline colour
# palette tool needs paletteline colour

# map editor changes tile paletteline
# tile editor changes tile colour
# palette tool changes paletteline colour

COLOUR_RAMP = [0, 29, 52, 70, 87, 101, 116, 130, 144, 158, 172, 187, 206, 228, 255]

event2canvas = lambda e, c: (c.canvasx(e.x), c.canvasy(e.y))

tile_height = 8

PPM_HEADER = b'P6 '
PPM_HEADER = PPM_HEADER + str(8).encode('ascii')
PPM_HEADER = PPM_HEADER + b' '
PPM_HEADER = PPM_HEADER + str(tile_height).encode('ascii')
PPM_HEADER = PPM_HEADER +  b' 255 '

BYTE_SIZE = 8

NIBBLE_SIZE = BYTE_SIZE >> 1

test_1 = False
        
PALETTE_TILE_SIZE = 32

char_list = [' ']

import ctypes
c_uint16 = ctypes.c_uint16

for i in range(26):
    char_list.append(chr(i + 65))
for i in range(26):
    char_list.append(chr(i + 97))
    
for i in range(10):
    char_list.append(chr(i + 48))
    
caret_mask = [
    1,1,1,1,1,0,0,0,
    1,2,1,2,1,0,0,0,
    0,1,2,1,0,0,0,0,
    0,1,2,1,0,0,0,0,
    0,1,2,1,0,0,0,0,
    0,1,2,1,0,0,0,0,
    1,2,1,2,1,0,0,0,
    1,1,1,1,1,0,0,0,
    ]
    
error_tile = [
    1,1,1,1,1,1,1,1,
    1,1,0,0,0,0,1,1,
    1,0,1,0,0,1,0,1,
    1,0,0,1,1,0,0,1,
    1,0,0,1,1,0,0,1,
    1,0,1,0,0,1,0,1,
    1,1,0,0,0,0,1,1,
    1,1,1,1,1,1,1,1,
    ]
    
    
error_ppm = array.array('B')
for i in range(len(error_tile)):
    error_ppm.append([0,255][error_tile[i]])
    error_ppm.append(0)
    error_ppm.append(0)
error_ppm = PPM_HEADER + error_ppm

class VDPFields( ctypes.LittleEndianStructure ): #PCCY XAAA AAAA AAAA
    _fields_ = [
        ("address",     c_uint16, 11 ),
        ("xflip",       c_uint16, 1 ),
        ("yflip",       c_uint16, 1 ),
        ("palette",     c_uint16, 2 ),
        ("priority",    c_uint16, 1 ),
        ]

class VDPIndex( ctypes.Union ):
    _anonymous_ = ("field",)
    _fields_ = [
        ("field",    VDPFields ),
        ("asWord", c_uint16    )
        ]

class Palette:
    
    def __init__(self, int_palette):
        self.int_palette = int_palette
        self.make_true_palette()
        
    def make_true_palette(self):
        self.true_palette = bytearray()
        self.true_palette_tk = []
        for line in range(4):
            line_r = []
            for i in range(16):
                r, g, b = self.get_rgb_colour(line, i)
                for c in [COLOUR_RAMP[r],COLOUR_RAMP[g],COLOUR_RAMP[b],0]:
                    self.true_palette.append(c)
                r, g, b = ["{0:0{1}x}".format(i,2) for i in [COLOUR_RAMP[r],COLOUR_RAMP[g],COLOUR_RAMP[b]]]
                line_r.append('#{}{}{}'.format(r,g,b))
            self.true_palette_tk.append(line_r)
            
    def get_true_rgb_colour(self, paletteline, colour):
        offset = (paletteline << 6) + (colour << 2)
        return(self.true_palette[offset:offset+3])
        
    def get_true_tk_colour(self, paletteline, colour):
        return(self.true_palette_tk[paletteline][colour])
        
    def get_rgb_colour(self, paletteline, colour):
        palettelineoffset = paletteline * 16
        bgr_offset = palettelineoffset + colour
        bgr = self.int_palette[bgr_offset]
        r = bgr & 0xF
        g = (bgr >> NIBBLE_SIZE) & 0xF
        b = bgr >> BYTE_SIZE
        return(r,g,b)
        
    def set_colour_from_rgb(self, paletteline, colour, rgb):
        palettelineoffset = paletteline * 16
        bgr_offset = palettelineoffset + colour
        r, g, b = rgb
        self.int_palette[bgr_offset] = r + (g << NIBBLE_SIZE) + (b << BYTE_SIZE)
                
        self.make_true_palette()
        root.event_generate('<<PaletteChanged>>')
        
class PaletteTool(tk.Canvas):
    
    def __init__(self, parent, palette, var_paletteline, var_colour, *args, **options):
        self.palette = palette
        self.paletteline = var_paletteline
        self.paletteline.trace('w',self.draw_selector)
        self.colour_index = var_colour
        self.colour_index.trace('w',self.draw_selector)
        tk.Canvas.__init__(self, parent, *args, **options)
        self.config(height = (PALETTE_TILE_SIZE * 4) + 1, width = (PALETTE_TILE_SIZE * 16)+1)
        self.rect1 = self.create_rectangle(0,0,16,16, fill='', outline="white", dash=[4,4])
        self.rect1id = self.find_closest(0, 0, halo=2)
        self.rect2 = self.create_rectangle(0,32,16,48, fill='', outline="white", dash=[4,4])
        self.rect2id = self.find_closest(0, 32, halo=2)
        
    def refresh(self):
        for line in range(4):
            for colour in range(16):
                x = colour*PALETTE_TILE_SIZE
                y = line*PALETTE_TILE_SIZE
                self.create_rectangle(x+1,y+1,x+PALETTE_TILE_SIZE,y+PALETTE_TILE_SIZE, fill=self.palette.get_true_tk_colour(line, colour), outline = '')
        self.draw_selector()
        for bind in ["<ButtonPress-1>", "<B1-Motion>"]:
            self.bind(bind, lambda event: self.clicked(event))
                
    def draw_selector(self, *args):
        r, g, b = self.palette.get_rgb_colour(self.paletteline.get(),self.colour_index.get())
        app.palette_r.current(r>>1)
        app.palette_g.current(g>>1)
        app.palette_b.current(b>>1)
        x = self.colour_index.get() * PALETTE_TILE_SIZE
        y = self.paletteline.get() * PALETTE_TILE_SIZE
        self.coords(self.rect1id, 0,y,PALETTE_TILE_SIZE*16,y+PALETTE_TILE_SIZE)
        self.coords(self.rect2id, x,0,x+PALETTE_TILE_SIZE,PALETTE_TILE_SIZE*4)
        
    def clicked(self, event):
        x, y = event2canvas(event, self)
        x = int(x / PALETTE_TILE_SIZE)
        y = int(y / PALETTE_TILE_SIZE)
        if x > 15:
            x = 15
        if y > 3:
            y = 3
        if x >= 0 and y >= 0:
            if self.paletteline.get() != y:
                self.paletteline.set(y)
            if self.colour_index.get() != x:
                self.colour_index.set(x)

class Tile:

    def __init__(self, int_tile, palette):
        self.palette = palette
        self.int_tile = bytearray(int_tile)
        ppm = tile_to_ppm(self.int_tile, 0, self.palette)
        self.variants = {(0,1): tkinter.PhotoImage(width=8, height=tile_height, data=ppm, format='PPM')}
        self.marked_dirty = []
        
    def variant(self, flags, zoom=1): # flags = PCCY XAAA
        oldflags = flags
        flags = flags & 15 #ignore the top bit, now flags = CCYX
        paletteline = (flags >> 2) & 3
        
        if (flags, zoom) not in self.variants or ((flags, zoom) in self.marked_dirty):
            try:
                self.marked_dirty.remove((flags,zoom))
            except:
                pass
            if zoom != 1:
                img = self.variant(oldflags)
                zoomed_img = img.zoom(zoom,zoom) # zoom zoom
                self.variants[(flags, zoom)] = zoomed_img
            else:
                yflip = (flags >> 1) & 1
                xflip = flags & 1
                ppm = tile_to_ppm(self.transform(xflip, yflip), paletteline, self.palette)
                img = tkinter.PhotoImage(data=ppm, format='PPM')
                self.variants[(flags, zoom)] = img
        return(self.variants[(flags, zoom)])
        
    def transform(self, xflip, yflip):
        rows = [self.int_tile[i:i+8] for i in range(0, len(self.int_tile), 8)]
        if yflip: #vertical flip
            rows = list(reversed(rows))
        if xflip: #horizontal flip
            new_rows = []
            for i in rows:
                new_rows.append(list(reversed(i)))
            rows = new_rows
        joined_rows = bytearray()
        for i in rows:
            joined_rows = joined_rows + bytearray(i)
        return(joined_rows)
        
    def putpixel(self, x, y, colour):
        try:
            colour = colour.get()
        except:
            pass
        pixelnum = (y*8)+x
        if self.int_tile[pixelnum] != colour:
            self.int_tile[pixelnum] = colour
            self.marked_dirty = []
            for key in list(self.variants.keys()):
                if key[1] != 1:
                    self.marked_dirty.append(key)
                    
                else:
                    flags = key[0]
                    zoom = key[1]
                    paletteline = (flags >> 2) & 3
                    newcolour = self.palette.get_true_tk_colour(paletteline, colour)
                    xflip = flags & 1
                    yflip = (flags >> 1) & 1
                    if xflip:
                        out_x = 7 - x
                    else:
                        out_x = x
                        
                    if yflip:
                        out_y = (tile_height - 1) - out_y
                    else:
                        out_y = y
                        
                    self.variants[flags,zoom].put(newcolour, to = (out_x,out_y))
            root.event_generate('<<PutPixel>>')

    def refresh_2(self):
        for i in self.marked_dirty:
            del self.variants[i]
        self.marked_dirty = []
        root.event_generate('<<LastPixel>>')
    
    def getpixel(self, x, y):
        pixelnum = (y*8)+x
        return(self.int_tile[pixelnum])
        
    def refresh(self, paletteline):
        smarked_dirty = []
        for key in list(self.variants.keys()):
            if (key[0] >> 2) == paletteline:
                smarked_dirty.append(key)
                
        for i in smarked_dirty:
            del self.variants[i]
    
def tile_to_ppm(tile, paletteline, palette, *args):
    ppm = bytearray()
    palettelineoffset = paletteline << 6 #16 * 4
    if tile == None or (None in args):
        ppm = error_ppm
    else:
        for y in range(tile_height):
            for x in range(8):
                i = (y << 3) + x
                pixel_value = tile[i]
                if args and pixel_value == 0:
                    r, g, b = palette.get_true_rgb_colour(args[1], args[0][i])
                else:
                    try:
                        r, g, b = palette.get_true_rgb_colour(paletteline, pixel_value)
                    except:
                        r, g, b = palette.get_true_rgb_colour(paletteline.get(), pixel_value)
                ppm.append(r)
                ppm.append(g)
                ppm.append(b)
        ppm = PPM_HEADER + ppm
    return(ppm)
    
def caret_on_ppm(ppm):
    d = 11
    header = PPM_HEADER
    new_ppm = array.array('B')
    for i in range(len(caret_mask)):
        for n in range(3):
            if caret_mask[i]:
                new_ppm.append([0,0,255][caret_mask[i]])
            else:
                new_ppm.append(ppm[d + (i * 3) + n])
    new_ppm = header + new_ppm
    return(new_ppm)
    
class Editor(tk.Frame):
    def __init__(self, parent, var_selector, *args, **options):
        tk.Frame.__init__(self, parent, *args, **options)
        self.config(borderwidth = 2, relief = tk.RAISED, padx = 4, pady = 4)
        self.selection = var_selector
        self.control_frame = tk.Frame(self)
        self.control_frame.grid()
        self.selector = ttk.Combobox(self.control_frame, state = ['readonly'], width = 2)
        self.selector.bind('<<ComboboxSelected>>', self.select_map)
        self.selector.grid()
        
    def select_map(self, event=''):
        self.selection.set(self.selector.current())
        self.refresh()
                
class FontTool(tk.Frame):
    def __init__(self, parent, tilelist, var_paletteline, var_tile, *args, **options):
        tk.Frame.__init__(self, parent, *args, **options)
        
        self.tilelist = tilelist
        self.paletteline = var_paletteline
        self.paletteline.trace('w',self.refresh)
        self.tile = var_tile
        self.tile.trace('w',lambda *args: self.tile_changed())
        
        self.lower_a_offset = 0
        self.upper_a_offset = 0
        self.space_offset = 0
        self.zero_offset = 0
        
        self.lower_a_toggle = tk.IntVar()
        self.upper_a_toggle = tk.IntVar()
        self.space_toggle = tk.IntVar()
        self.zero_toggle = tk.IntVar()
        
        tk.Label(self, text = "Lowercase A:").grid(column = 0, row = 0)
        self.lower_a_cmb = ttk.Combobox(self, state = ['readonly'], width = 2)
        self.lower_a_cmb.grid(column = 1, row = 0)
        self.lower_a_btn = tk.Checkbutton(self, indicatoron = False, variable = self.lower_a_toggle)
        self.lower_a_btn.grid(column = 2, row = 0)
        
        tk.Label(self, text = "Uppercase A:").grid(column = 0, row = 1)
        self.upper_a_cmb = ttk.Combobox(self, state = ['readonly'], width = 2)
        self.upper_a_cmb.grid(column = 1, row = 1)
        self.upper_a_btn = tk.Checkbutton(self, indicatoron = False, variable = self.upper_a_toggle)
        self.upper_a_btn.grid(column = 2, row = 1)
        
        tk.Label(self, text = "Space:").grid(column = 0, row = 2)
        self.space_cmb = ttk.Combobox(self, state = ['readonly'], width = 2)
        self.space_cmb.grid(column = 1, row = 2)
        self.space_btn = tk.Checkbutton(self, indicatoron = False, variable = self.space_toggle)
        self.space_btn.grid(column = 2, row = 2)
        
        tk.Label(self, text = "Zero:").grid(column = 0, row = 3)
        self.zero_cmb = ttk.Combobox(self, state = ['readonly'], width = 2)
        self.zero_cmb.grid(column = 1, row = 3)
        self.zero_btn = tk.Checkbutton(self, indicatoron = False, variable = self.zero_toggle)
        self.zero_btn.grid(column = 2, row = 3)
        
        self.lower_a_cmb.bind('<<ComboboxSelected>>', self.combo_changed)
        self.upper_a_cmb.bind('<<ComboboxSelected>>', self.combo_changed)
        self.space_cmb.bind('<<ComboboxSelected>>', self.combo_changed)
        self.zero_cmb.bind('<<ComboboxSelected>>', self.combo_changed)
        
        self.tile_changed()
        
    def combo_to_offset(self):
        self.lower_a_offset = self.lower_a_cmb.current()
        self.upper_a_offset = self.upper_a_cmb.current()
        self.space_offset = self.space_cmb.current()
        self.zero_offset = self.zero_cmb.current()
        
    def combo_changed(self, *args):
        self.combo_to_offset()
        self.refresh()
        
    def refresh(self, *args):
        tile_choices = []
        for i in range(len(self.tilelist)):
            tile_choices.append(format(i*(tile_height >> 3),'x'))
        for x, y, z in [
            [self.lower_a_cmb,self.lower_a_offset, self.lower_a_btn],
            [self.upper_a_cmb,self.upper_a_offset, self.upper_a_btn],
            [self.space_cmb,self.space_offset, self.space_btn],
            [self.zero_cmb,self.zero_offset, self.zero_btn],
            ]:
            x.config(values = tile_choices)
            if y < len(tile_choices):
                x.current(y)
            else:
                x.current(0)
            z.config(image = self.tilelist[x.current()].variant(self.paletteline.get() << 2,4))
            
        
    def tile_changed(self, *args):
        if self.lower_a_toggle.get():
            self.lower_a_offset = self.tile.get()
        if self.upper_a_toggle.get():
            self.upper_a_offset = self.tile.get()
        if self.space_toggle.get():
            self.space_offset = self.tile.get()
        if self.zero_toggle.get():
            self.zero_offset = self.tile.get()
            
        self.disable_selection()
            
        self.refresh()
        self.combo_to_offset()
        
    def disable_selection(self):
        for i in [self.lower_a_toggle, self.upper_a_toggle, self.zero_toggle, self.space_toggle]:
            i.set(0)
            
class VerticalScrolledFrame(tk.Frame):
    """A pure Tkinter scrollable frame that actually works!
    * Use the 'interior' attribute to place widgets inside the scrollable frame
    * Construct and pack/place/grid normally
    * This frame only allows vertical scrolling

    """
    def __init__(self, parent, *args, **kw):
        tk.Frame.__init__(self, parent, *args, **kw)            

        # create a canvas object and a vertical scrollbar for scrolling it
        vscrollbar = tk.Scrollbar(self, orient=tk.VERTICAL)
        vscrollbar.pack(fill=tk.Y, side=tk.RIGHT, expand=tk.FALSE)
        canvas = tk.Canvas(self, bd=0, background = '#FFFFFF', highlightthickness=0,
                        yscrollcommand=vscrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=tk.TRUE)
        vscrollbar.config(command=canvas.yview)

        # reset the view
        canvas.xview_moveto(0)
        canvas.yview_moveto(0)

        # create a frame inside the canvas which will be scrolled with it
        self.interior = interior = tk.Frame(canvas)
        interior_id = canvas.create_window(0, 0, window=interior,
                                           anchor=tk.NW)
        
        self.canvas = canvas

        # track changes to the canvas and frame width and sync them,
        # also updating the scrollbar
        def _configure_interior(event):
            # update the scrollbars to match the size of the inner frame
            size = (interior.winfo_reqwidth(), interior.winfo_reqheight())
            canvas.config(scrollregion="0 0 %s %s" % size)
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # update the canvas's width to fit the inner frame
                canvas.config(width=interior.winfo_reqwidth())
        interior.bind('<Configure>', _configure_interior)
        
        def _bound_to_mousewheel(event):
            self.canvas.bind_all("<MouseWheel>", _on_mousewheel)   

        def _unbound_to_mousewheel(event):
            self.canvas.unbind_all("<MouseWheel>") 

        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        self.bind('<Enter>', _bound_to_mousewheel)
        self.bind('<Leave>', _unbound_to_mousewheel)
        
class ScrolledFrame(tk.Frame):
    """A pure Tkinter scrollable frame that actually works!
    * Use the 'interior' attribute to place widgets inside the scrollable frame
    * Construct and pack/place/grid normally
    * This frame only allows vertical scrolling

    """
    def __init__(self, parent, *args, **kw):
        tk.Frame.__init__(self, parent, *args, **kw)            

        # create a canvas object and a vertical scrollbar for scrolling it
        vscrollbar = tk.Scrollbar(self, orient=tk.VERTICAL)
        hscrollbar = tk.Scrollbar(self, orient=tk.HORIZONTAL)
        vscrollbar.grid(column = 1, sticky = 'nsew')#pack(fill=tk.Y, side=tk.RIGHT, expand=tk.FALSE)
        canvas = tk.Canvas(self, bd=0, background = '#FFFFFF', highlightthickness=0,
                        yscrollcommand=vscrollbar.set, xscrollcommand=hscrollbar.set)
        canvas.grid(column = 0, row = 0, sticky = 'nsew')#pack(side=tk.LEFT, fill=tk.BOTH, expand=tk.TRUE)
        hscrollbar.grid(row = 1, sticky = 'nsew')#pack(fill=tk.X, side=tk.BOTTOM, expand=tk.FALSE)
        vscrollbar.config(command=canvas.yview)
        hscrollbar.config(command=canvas.xview)

        # reset the view
        canvas.xview_moveto(0)
        canvas.yview_moveto(0)

        # create a frame inside the canvas which will be scrolled with it
        self.interior = interior = tk.Frame(canvas)
        interior_id = canvas.create_window(0, 0, window=interior,
                                           anchor=tk.NW)
                                           
        canvas.config(width = 40*16, height = 28*16)
        
        self.canvas = canvas
        
        # track changes to the canvas and frame width and sync them,
        # also updating the scrollbar
        def _configure_interior(event):
            # update the scrollbars to match the size of the inner frame
            width = (interior.winfo_reqwidth(), interior.winfo_reqheight())
            #canvas.config(scrollregion="0 0 %s %s" % size)
            canvas.config(scrollregion=canvas.bbox("all"))
        interior.bind('<Configure>', _configure_interior)
        
        def _bound_to_mousewheel(event):
            self.canvas.bind_all("<MouseWheel>", _on_mousewheel)   

        def _unbound_to_mousewheel(event):
            self.canvas.unbind_all("<MouseWheel>") 

        def _on_mousewheel(event):
            s = event.state
            # Manual way to get the modifiers
            ctrl  = (s & 0x4) != 0
            if ctrl:
                self.canvas.xview_scroll(int(-1*(event.delta/120)), "units")
            else:
                self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        self.bind('<Enter>', _bound_to_mousewheel)
        self.bind('<Leave>', _unbound_to_mousewheel)

            
class TileBrowser(VerticalScrolledFrame):
    def __init__(self, parent, tilelist, var_tile, var_paletteline, *args, **options):
        VerticalScrolledFrame.__init__(self, parent, *args, **options)
        self.tilelist = tilelist
        self.tile = var_tile
        self.paletteline = var_paletteline
        self.paletteline.trace('w',lambda *args: self.refresh())
        self.images = []
        self.tiles = []
        
    def refresh(self, *tile):
        if not tile:
            self.images = []
            for i in self.tilelist:
                self.images.append(i.variant(self.paletteline.get() << 2, zoom = 2))
            if len(self.images) > len(self.tiles):
                for i in range(len(self.images) - len(self.tiles)):
                    self.tiles.append(tk.Label(self.interior, text = '', borderwidth=0))
                    for bind in ["<ButtonPress-1>", "<B1-Motion>", "<ButtonPress-3>", "<B3-Motion>"]:
                        self.tiles[-1].bind(bind, lambda event: self.select_tile(event))
            elif len(self.images) < len(self.tiles):
                for i in range(len(self.tiles) - len(self.images)):
                    self.tiles[0-(i + 1)].grid_forget()
            for i in range(len(self.images)):
                self.tiles[i].grid(column = i % 8, row = i >> 3)
                self.tiles[i].config(image = self.images[i])
                
    def select_tile(self, event = ''):
        x = self.interior.winfo_pointerx() - self.interior.winfo_rootx()
        y = self.interior.winfo_pointery() - self.interior.winfo_rooty()
        x = x >> 4
        y = (y >> 4) << 3
        i = y + x
        
        if 0 <= i < len(self.images):
            self.tile.set(i)
        
class PlaneMapEditor(Editor):

    def __init__(self, parent, var_selector, palette, tilelist, var_tile, var_paletteline, planes, var_plane_map_width, var_plane_map_height, *args, **options):
        Editor.__init__(self, parent, var_selector, *args, **options)
        self.plane_map_width = var_plane_map_width
        self.plane_map_height = var_plane_map_height
        self.paletteline = var_paletteline
        self.planes = planes
        self.tilelist = tilelist
        self.palette = palette
        self.tool = 0
        self.tile = var_tile
        self.selector.config(values = ['Plane A', 'Plane B', 'Both'], width = 7)
        self.selector.current(0)
        self.viewer_portal = ScrolledFrame(self)
        self.viewer_portal.grid(column = 1, row = 0, rowspan = 2, sticky='nsew')
        self.viewer = MapViewer(self.viewer_portal.interior, self.plane_map_width.get(), self.plane_map_height.get(), self.tilelist, height = self.plane_map_height.get()*16, width = self.plane_map_width.get()*16, bd=0, highlightthickness = 0)
        #self.viewer.grid(column = 1, row = 0, rowspan = 2)
        self.viewer.grid()
        for bind in ["<ButtonPress-1>", "<B1-Motion>"]:
            self.viewer.bind(bind, lambda event: self.clicked(event))
        for bind in ["<ButtonPress-3>", "<Control-Button-1>", "<B3-Motion>", "<Control-B1-Motion>"]:
            self.viewer.bind(bind, lambda event: self.rightclicked(event))
            
        root.bind('<Key>', lambda event: self.keyboard(event))
        self.xflip = tk.IntVar()
        self.yflip = tk.IntVar()
        self.priority = tk.IntVar()
        
        control_frame = tk.Frame(self)
        control_frame.grid(column = 0, row = 1)
        
        vcmd = (root.register(self.validate),
            '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')
        
        self.var_height = tk.StringVar()
        self.var_width = tk.StringVar()
        
        self.var_height.set(str(28))
        self.var_width.set(str(40))
        
        tk.Label(control_frame, text = "Width").grid()
        self.ent_width = tk.Entry(control_frame, textvariable = self.var_width, width = 3, validate = 'key', validatecommand = vcmd)
        self.ent_width.grid(column = 1, row = 0)
        
        tk.Label(control_frame, text = "Height").grid()
        self.ent_height = tk.Entry(control_frame, textvariable = self.var_height, width = 3, validate = 'key', validatecommand = vcmd)
        self.ent_height.grid(column = 1, row = 1)
        
        self.var_height.trace('w',self.change_size)
        self.var_width.trace('w',self.change_size)
        
        self.chk_priority = tk.Checkbutton(control_frame, text = "Priority", variable = self.priority)#, onvalue = 1 << 15)
        self.chk_priority.grid(columnspan = 2)
        
        self.chk_xflip = tk.Checkbutton(control_frame, text = "X flip", variable = self.xflip)#, onvalue = 1 << 11)
        self.chk_xflip.grid(columnspan = 2)
        self.chk_yflip = tk.Checkbutton(control_frame, text = "Y flip", variable = self.yflip)#, onvalue = 1 << 12)
        self.chk_yflip.grid(columnspan = 2)
        self.deeptiles = {}
        self.caret_tile = None
        self.caret_pos = None
        
    def change_size(self, *args):
        if (self.var_width.get() != '') and (self.var_height.get() != ''):
            for plane in self.planes:
                diff = (int(self.var_width.get()) * int(self.var_height.get())) - len(plane)
                if diff > 0:
                    for i in range(diff):
                        plane.append(VDPIndex())
            self.plane_map_width.set(int(self.var_width.get()))
            self.plane_map_height.set(int(self.var_height.get()))
            self.viewer.change_size(int(self.var_width.get()), int(self.var_height.get()))
            self.refresh()
        
    def validate(self, action, index, value_if_allowed,
                       prior_value, text, validation_type, trigger_type, widget_name):
        try:
            int_value_if_allowed = int(value_if_allowed)
        except:
            int_value_if_allowed = 1
        if int_value_if_allowed == 0:
            return False
        elif value_if_allowed == '':
            return True
        elif value_if_allowed:
            try:
                int(value_if_allowed)
                return True
            except ValueError:
                return False
        else:
            return False
        
    def keyboard(self, event):
        if self.tool and self.caret_pos:
            if event.char in char_list:
                s = event.state

                # Manual way to get the modifiers
                #ctrl  = (s & 0x4) != 0
                #alt   = (s & 0x8) != 0 or (s & 0x80) != 0
                shift = (s & 0x1) != 0
                caps = (s & 0x2) != 0
                char = event.char
                if shift ^ caps:
                    char = char.upper()
                chari = ord(char)
                sel = self.selection.get() % 2
                offset = (self.caret_pos[0] * self.plane_map_width.get()) + self.caret_pos[1]
                thistile = self.planes[sel][offset]
                if char == ' ':
                    thistile.address = app.font_tool.space_offset
                elif chari < 58:
                    thistile.address = app.font_tool.zero_offset + (chari - 48)
                elif chari > 96:
                    thistile.address = app.font_tool.lower_a_offset + (chari - 97)
                else:
                    thistile.address = app.font_tool.upper_a_offset + (chari - 65)
                thistile.priority = self.priority.get()
                thistile.xflip = self.xflip.get()
                thistile.yflip = self.yflip.get()
                thistile.palette = self.paletteline.get()
                self.caret_pos[1] = self.caret_pos[1] + 1
                if self.caret_pos[1] > 39:
                    self.caret_pos[1] = 0
                    self.caret_pos[0] = (self.caret_pos[0] + 1) % self.plane_map_height.get()
                self.refresh()
        
    def clicked(self, event):
        cx, cy = event2canvas(event, self.viewer)
        cx = int(cx) >> 4
        cy = int(cy) >> 4
        if 0 <= cx < self.plane_map_width.get() and 0 <= cy < self.plane_map_height.get():
            if self.tool == 0:
                sel = self.selection.get()
                sel = sel % 2
            #PCCY XAAA AAAA AAAA
                offset = (cy * self.plane_map_width.get()) + cx
                thistile = self.planes[sel][offset]
                thistile.address = self.tile.get()
                thistile.priority = self.priority.get()
                thistile.xflip = self.xflip.get()
                thistile.yflip = self.yflip.get()
                thistile.palette = self.paletteline.get()
            elif self.tool == 1:
                try:
                    old_caret_pos = copy.deepcopy(self.caret_pos)
                except:
                    pass
                self.caret_pos = [cy, cx]
                try:
                    self.refresh(x = old_caret_pos[1], y = old_caret_pos[0])
                except:
                    pass
            self.refresh(x=cx,y=cy)
        
    def rightclicked(self, event):
        cx, cy = event2canvas(event, self.viewer)
        cx = int(cx) >> 4
        cy = int(cy) >> 4
        if 0 <= cx < self.plane_map_width.get() and 0 <= cy < self.plane_map_height.get():
            sel = self.selection.get()
            sel = sel % 2
            offset = (cy * self.plane_map_width.get()) + cx
            thistile = self.planes[sel][offset]
            if thistile.xflip:
                self.chk_xflip.select()
            else:
                self.chk_xflip.deselect()
            if thistile.yflip:
                self.chk_yflip.select()
            else:
                self.chk_yflip.deselect()
            if thistile.priority:
                self.chk_priority.select()
            else:
                self.chk_priority.deselect()
            self.paletteline.set(thistile.palette)
            if thistile.address < len(self.tilelist):
                self.tile.set(thistile.address)
            
    def refresh(self, x=None, y=None):
        if self.selection.get() < 2:
            self.viewer.refresh(self.planes[self.selection.get()], x, y)
        else:
            self.deeptiles = {}
            for y in range(self.plane_map_height.get()):
                offset_y = y * self.plane_map_width.get()
                for x in range(self.plane_map_width.get()):
                    offset = offset_y + x
                    key = (self.planes[0][offset].asWord, self.planes[1][offset].asWord)
                    if key not in self.deeptiles:
                        tiles = []
                        palettelines = []
                        priority = 0
                        for i in range(2):
                            tile = self.planes[i][offset]
                            palettelines.append(tile.palette)
                            try:
                                tiles.append(self.tilelist[tile.address].transform(tile.xflip, tile.yflip))
                            except IndexError:
                                tiles.append(None)
                            priority = tile.priority
                        if priority > 0:
                            ppm = tile_to_ppm(tiles[1], palettelines[1], self.palette, tiles[0], palettelines[0])
                        else:
                            ppm = tile_to_ppm(tiles[0], palettelines[0], self.palette, tiles[1], palettelines[1])
                        img = tkinter.PhotoImage(data=ppm, format='PPM')
                        img = img.zoom(2,2)
                        self.deeptiles[key] = img
                        
                    self.viewer.itemconfigure(self.viewer.tiles[offset], image = self.deeptiles[key])
        if self.tool and self.caret_pos:
            y = self.caret_pos[0]
            x = self.caret_pos[1]
            offset = (y * self.plane_map_width.get()) + x
            tile = self.planes[1][offset]
            ppm = caret_on_ppm(tile_to_ppm(self.tilelist[tile.address].transform(tile.xflip, tile.yflip), tile.palette, self.palette))
            img = tkinter.PhotoImage(data=ppm, format='PPM')
            self.caret_tile = img.zoom(2,2)
            self.viewer.itemconfigure(self.viewer.tiles[offset], image = self.caret_tile)
        
class MapViewer(tk.Canvas):
    
    def __init__(self, parent, width_t, height_t, tilelist, *args, **options):
        tk.Canvas.__init__(self, parent, *args, **options)
        self.tilelist = tilelist
        
        self.width_t = width_t
        self.height_t   = height_t
        
        self.tiles = []
        for y in range(self.height_t):
            for x in range(self.width_t):
                tile = self.create_image(x*16,y*16, anchor = tk.NW)
                self.tiles.append(tile)
            
        self.error_image = tkinter.PhotoImage(width=8, height=8, data=error_ppm, format='PPM')
        self.error_image = self.error_image.zoom(2,2)
            
    def refresh(self, hex_split, x, y): #PCCY XAAA AAAA AAAA
        if not x:
            for y in range(self.height_t):
                offset_y = y * self.width_t
                for x in range(self.width_t):
                    offset = x + offset_y
                    thistile = hex_split[offset]
                    tileflags = (thistile.asWord >> 11) & 0b11111
                    try:
                        self.itemconfigure(self.tiles[offset], image = self.tilelist[thistile.address].variant(tileflags, 2))
                    except IndexError:
                        self.itemconfigure(self.tiles[offset], image = self.error_image)
        else:
            offset = x + (y * self.width_t)
            thistile = hex_split[offset]
            tileflags = (thistile.asWord >> 11) & 0b11111
            try:
                self.itemconfigure(self.tiles[offset], image = self.tilelist[thistile.address].variant(tileflags, 2))
            except IndexError:
                self.itemconfigure(self.tiles[offset], image = self.error_image)
                
    def refresh_2(self, hex_split, hex_split_2):
        pass
        
    def change_size(self, width, height):
        self.width_t = width
        self.height_t = height
        self.config(width = width * 16, height = height * 16)
        x = 0
        y = 0
        count = 0
        for tile in self.tiles:
            cur_coords = self.coords(tile)
            cur_x = cur_coords[0]
            cur_y = cur_coords[1]
            self.move(tile, (x * 16) - cur_x, (y * 16) - cur_y)
            x = (x + 1) % width
            if x == 0:
                y = y + 1
            count = count + 1
        new_tiles = (width * height) - count
        if new_tiles > 0:
            for i in range(new_tiles):
                tile = self.create_image(x*16,y*16, anchor = tk.NW)
                self.tiles.append(tile)
                x = (x + 1) % width
                if x == 0:
                    y = y + 1
        elif new_tiles < 0:
            for i in range(new_tiles):
                self.delete(self.tiles[-1])
                del self.tiles[-1]

class TileEditor(Editor):

    def __init__(self, parent, var_selector, tilelist, var_tile, var_paletteline, var_colour, *args, **options):
        Editor.__init__(self, parent, var_selector, *args, **options)
        self.tilelist = tilelist
        self.selected_colour = var_colour
        self.paletteline = var_paletteline
        self.canvas = tk.Canvas(self, bd=0, height = tile_height*16, width = 8*16, bg="WHITE", highlightthickness = 0)
        self.canvas.grid(column = 1, row = 0)
        self.viewer = tk.Label(self.canvas, text = '', borderwidth=0)
        self.viewer.grid()
        for bind in ["<ButtonPress-1>", "<B1-Motion>"]:
            self.viewer.bind(bind, lambda event: self.clicked(event))
        for bind in ["<ButtonPress-3>", "<Control-Button-1>", "<B3-Motion>", "<Control-B1-Motion>"]:
            self.viewer.bind(bind, lambda event: self.rightclicked(event))
        self.add_tile = tk.Button(self.control_frame, text='New tile', command = self.add_tile)
        self.add_tile.grid()
        self.remove_tile = tk.Button(self.control_frame, text='Delete tile', command = self.remove_tile, state = tk.DISABLED)
        self.remove_tile.grid()
        for bind in ["<ButtonRelease-1>"]:
            self.viewer.bind(bind, lambda event: self.unclicked(event))
            
        self.selection.trace('w',self.tile_selected)
        self.paletteline.trace('w',self.refresh)
        
    def tile_selected(self, *args):
        self.selector.current(self.selection.get())
        self.refresh()
            
    def unclicked(self, event):
        self.tilelist[self.selection.get()].refresh_2()
        
    def clicked(self, event):
        cx, cy = event2canvas(event, self.canvas)
        cx = int(cx) >> 4
        cy = int(cy) >> 4
        if 0 <= cx < 8 and 0 <= cy < tile_height:
            self.tilelist[self.selection.get()].putpixel(cx,cy,self.selected_colour.get())
        
    def rightclicked(self, event):
        cx, cy = event2canvas(event, self.canvas)
        cx = int(cx) >> 4
        cy = int(cy) >> 4
        if cx < 8 and cy < tile_height:
            self.selected_colour.set(self.tilelist[self.selection.get()].getpixel(cx,cy))
        
    def refresh(self, *args):
        self.viewer.config(image = self.tilelist[self.selection.get()].variant(self.paletteline.get() << 2 , zoom = 16))
        return()
        
    def add_tile(self):
        self.tilelist.append(Tile([0] * (8 * 8), self.tilelist[0].palette))
        tile_choices = []

        for i in range(len(self.tilelist)):
            tile_choices.append(format(i*(tile_height >> 3),'x'))
            self.selector.config(values = tile_choices)
        #tile_choices.append(format(len(tile_choices),'x'))
        self.selector.config(values = tile_choices)
        self.remove_tile.config(state = tk.NORMAL)
        
        root.event_generate('<<TilesChanged>>')
        
    def remove_tile(self):
        del self.tilelist[self.selection.get()]
        #del tile_choices[-1]
        tile_choices = []

        for i in range(len(self.tilelist)):
            tile_choices.append(format(i*(tile_height >> 3),'x'))
            self.selector.config(values = tile_choices)
            
        if self.selection.get() >= len(tile_choices):
            self.selection.set(self.selection.get()-1)
            self.selector.current(self.selection.get())
        self.refresh()
        self.selector.config(values = tile_choices)
        if len(tile_choices) < 2:
            self.remove_tile.config(state = tk.DISABLED)
            
        root.event_generate('<<TilesChanged>>')
        
class App:

    def __init__(self, master):
        self.master = master
        self.frame = tk.Frame(master)
        self.frame.pack(expand = 1, fill = tk.BOTH)
        
        self.tile = tk.IntVar()
        self.tile.set(0)
        
        self.plane_map_width = tk.IntVar()
        self.plane_map_width.set(40)
        
        self.plane_map_height = tk.IntVar()
        self.plane_map_height.set(28)
        
        self.menubar = tk.Menu(self.frame)

        self.filemenu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label='File', menu=self.filemenu)
        self.frame.master.config(menu=self.menubar)
        
        self.filemenu.add_command(label='Open palette...', command=self.open_palette)
        self.filemenu.add_command(label='Open tiles...', command=self.open_tiles)
        self.filemenu.add_command(label='Open plane A...', command=self.open_mapa)
        self.filemenu.add_command(label='Open plane B...', command=self.open_mapb)
        self.filemenu.add_separator()
        self.filemenu.add_command(label='Save palette as...', command=self.save_palette)
        self.filemenu.add_command(label='Save tiles as...', command=self.save_tiles)
        self.filemenu.add_command(label='Save plane A as...', command=self.save_mapa)
        self.filemenu.add_command(label='Save plane B as...', command=self.save_mapb)
        
        self.palette_frame = tk.Frame(self.frame, borderwidth = 2, relief = tk.RAISED, padx = 4, pady = 4)
        self.palette_frame.pack(fill = tk.X,expand = 1)
        
        self.palette_r = ttk.Combobox(self.palette_frame, state = ['readonly'], width = 1)
        self.palette_r.grid(row=0)
        self.palette_g = ttk.Combobox(self.palette_frame, state = ['readonly'], width = 1)
        self.palette_g.grid(row=1)
        self.palette_b = ttk.Combobox(self.palette_frame, state = ['readonly'], width = 1)
        self.palette_b.grid(row=2)
        
        int_palette = [0] * 64
        self.palette = Palette(int_palette)

        self.tilelist = [Tile([0] * 64, self.palette),Tile([1] * 64, self.palette)]

        self.map = []

        for y in range(self.plane_map_height.get()):
            #row = []
            for x in range(self.plane_map_width.get()):
                self.map.append(VDPIndex())
                self.map[-1].yflip = y & 1
                self.map[-1].address = x & 1
            #self.map.append(row)

        self.map2 = copy.deepcopy(self.map)

        self.planes = [self.map, self.map2]
        
        
        self.paletteline = tk.IntVar()
        self.paletteline.set(0)
        self.colour = tk.IntVar()
        self.colour.set(0)
        
        self.palette_r.bind('<<ComboboxSelected>>', self.change_palette)
        self.palette_g.bind('<<ComboboxSelected>>', self.change_palette)
        self.palette_b.bind('<<ComboboxSelected>>', self.change_palette)
        
        self.palette_tool = PaletteTool(self.palette_frame, self.palette, self.paletteline, self.colour, borderwidth=0, highlightthickness=0, bg="BLACK")
        self.palette_tool.grid(row = 0, column = 1, rowspan = 3)
        
        rgb_values = []
        for i in range(8):
            rgb_values.append(format(i*2, 'x'))
            
        self.palette_r.config(values = rgb_values)
        self.palette_g.config(values = rgb_values)
        self.palette_b.config(values = rgb_values)
        
        self.selected_map = tk.IntVar()
        self.selected_map.set(0)
        
        self.tile_editor_frm = tk.Frame(self.frame)
        self.tile_editor = TileEditor(self.tile_editor_frm, self.tile, self.tilelist, self.tile, self.paletteline, self.colour)
        
        self.font_tool = FontTool(self.tile_editor_frm, self.tilelist, self.paletteline, self.tile)
        
        self.map_editor = PlaneMapEditor(self.frame, self.selected_map, self.palette, self.tilelist, self.tile, self.paletteline, self.planes, self.plane_map_width, self.plane_map_height)
        self.map_editor.pack(side=tk.LEFT, fill = tk.BOTH)
        self.tile_editor_frm.pack(side=tk.LEFT, fill = tk.Y)
        self.tool_selector = ttk.Combobox(self.tile_editor_frm, state = ['readonly'])
        self.tool_selector.bind('<<ComboboxSelected>>', self.select_tool)
        self.tool_selector.config(values = ['Tile', 'Text'])
        self.tool_selector.current(0)
        self.tool_selector.pack()
        self.tile_editor.pack(fill = tk.Y, expand = 1)
        self.tile_browser = TileBrowser(self.frame, self.tilelist, self.tile, self.paletteline)
        self.tile_browser.pack(fill = tk.BOTH, expand = 1)
        
        
        self.button = tk.Button(
            self.frame, text="QUIT", fg="red", command=self.frame.quit
            )

        tile_choices = []

        for i in range(len(self.tilelist)):
            tile_choices.append(format(i*(tile_height >> 3),'x'))
            self.tile_editor.selector.config(values = tile_choices)

        self.tile_editor.selector.current(0)
        
        self.master.bind('<<PaletteChanged>>', lambda event: self.palette_changed())
        self.master.bind('<<PutPixel>>', lambda event: self.put_pixel())
        self.master.bind('<<LastPixel>>', lambda event: self.last_pixel())
        self.master.bind('<<TilesChanged>>', lambda event: self.tiles_changed())
        
    def select_tool(self, event=''):
        tool = self.tool_selector.current()
        self.map_editor.tool = tool
        if tool == 0:
            self.font_tool.forget()
            self.tile_editor.pack(fill = tk.Y, expand = 1)
            self.font_tool.disable_selection()
        elif tool == 1:
            self.tile_editor.forget()
            self.font_tool.pack(fill = tk.Y, expand = 1)
        
    def change_palette(self, event=''):
        rgb = (self.palette_r.current()*2, self.palette_g.current()*2, self.palette_b.current()*2)
        self.palette.set_colour_from_rgb(self.paletteline.get(), self.colour.get(), rgb)
        
    def tiles_changed(self):
        self.tile_browser.refresh()
        self.map_editor.refresh()
        self.font_tool.refresh()
        
    def open_tiles(self):
        filename = tk.filedialog.askopenfilename(title = "Open tiles",filetypes = (("BIN files","*.bin"),("all files","*.*")))
        if filename !='':
            try:
                self.tilelist.clear()
                with open(filename, 'rb') as f:
                    thisdata = f.read()
                for tile in range(0,len(thisdata),32):
                    tiledata = [[i>>4,i&0xF] for i in thisdata[tile:tile+32]]
                    tiledata_2 = []
                    for this_list in tiledata:
                        tiledata_2.extend(this_list)
                    self.tilelist.append(Tile(tiledata_2, self.palette))
            except:
                pass
                
            tile_choices = []

            for i in range(len(self.tilelist)):
                tile_choices.append(format(i*(tile_height >> 3),'x'))
                self.tile_editor.selector.config(values = tile_choices)

            self.tile_editor.selector.current(0)
            
            self.map_editor.refresh()

            self.tile_editor.refresh()
            
            self.tile_browser.refresh()
            
            self.font_tool.refresh()
            
    def open_mapa(self):
        filename = tk.filedialog.askopenfilename(title = "Open plane A", filetypes = (("BIN files","*.bin"),("all files","*.*")))
        if filename !='':
            map = []
            with open(filename, 'rb') as binary_file:
                data = binary_file.read()
            for y in range(0, len(data), 2):
                map.append(VDPIndex())
                map[-1].asWord = (data[y] << 8) + data[y + 1]
            diff = (self.plane_map_height.get() * self.plane_map_width.get()) - len(map)
            for i in range(diff > 0 and diff):
                map.append(VDPIndex())
            self.planes[0] = map
            self.map_editor.refresh()
            
    def open_mapb(self):
        filename = tk.filedialog.askopenfilename(title = "Open plane B",filetypes = (("BIN files","*.bin"),("all files","*.*")))
        if filename !='':
            map = []
            with open(filename, 'rb') as binary_file:
                data = binary_file.read()
            for y in range(0, len(data), 2):
                map.append(VDPIndex())
                map[-1].asWord = (data[y] << 8) + data[y + 1]
            diff = (self.plane_map_height.get() * self.plane_map_width.get()) - len(map)
            for i in range(diff > 0 and diff):
                map.append(VDPIndex())
            self.planes[1] = map
            self.map_editor.refresh()
        
    def open_palette(self):
        filename = tk.filedialog.askopenfilename(title = "Open tiles",filetypes = (("BIN files","*.bin"),("all files","*.*")))
        if filename !='':
            palette = []
            with open(filename, 'rb') as binary_file:
                data = binary_file.read()
            for i in range(0, len(data), 2):
                palette.append((data[i] << 8) + data[i + 1])
            self.palette.int_palette = palette
            self.palette.make_true_palette()
            self.palette_tool.refresh()
            
    def save_mapa(self):
        filename = tk.filedialog.asksaveasfilename(title = "Save plane A", initialfile = "plane_a.bin", filetypes = (("BIN files","*.bin"),("all files","*.*")))
        if filename !='':
            out = array.array('B')
            for i in range(self.plane_map_height.get() * self.plane_map_width.get()):
                y = self.planes[0][i]
                #for x in y:
                out.append(y.asWord>>8)
                out.append(y.asWord&0xFF)
        
        with open(filename, "wb") as binary_file:
            binary_file.write(out)
            
    def save_mapb(self):
        filename = tk.filedialog.asksaveasfilename(title = "Save plane B", initialfile = "plane_b.bin", filetypes = (("BIN files","*.bin"),("all files","*.*")))
        if filename !='':
            out = array.array('B')
            for i in range(self.plane_map_height.get() * self.plane_map_width.get()):
                y = self.planes[1][i]
                #for x in y:
                out.append(y.asWord>>8)
                out.append(y.asWord&0xFF)
        
        with open(filename, "wb") as binary_file:
            binary_file.write(out)
        
    def save_palette(self):
        filename = tk.filedialog.asksaveasfilename(title = "Save palette",filetypes = (("BIN files","*.bin"),("all files","*.*")))
        if filename !='':
            out = array.array('B')
            for i in self.palette.int_palette:
                out.append(i>>8)
                out.append(i&0xFF)
        
        with open(filename, "wb") as binary_file:
            binary_file.write(out)
        
    def save_tiles(self):
        filename = tk.filedialog.asksaveasfilename(title = "Save tiles",filetypes = (("BIN files","*.bin"),("all files","*.*")))
        if filename !='':
            out = array.array('B')
            for tile in self.tilelist:
                for i in range(0, len(tile.int_tile), 2):
                    out.append((tile.int_tile[i] << 4) + tile.int_tile[i+1])
        
        with open(filename, "wb") as binary_file:
            binary_file.write(out)
            
    def palette_changed(self):
        self.palette_tool.refresh()
        for i in self.tilelist:
            i.refresh(self.paletteline.get())
        self.tile_editor.refresh()
        self.tile_browser.refresh()
        self.map_editor.refresh()
        self.font_tool.refresh()
        
    def put_pixel(self):
        self.tile_editor.refresh()
        
    def last_pixel(self):
        self.map_editor.refresh()
        self.tile_browser.refresh()
        self.font_tool.refresh()

root = tk.Tk()

app = App(root)

app.palette_tool.refresh()

app.tile_browser.refresh()
    
app.map_editor.refresh()

app.tile_editor.refresh()

root.mainloop()