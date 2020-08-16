import tkinter as tk
import tkinter.ttk as ttk
import tkinter.filedialog
import array
import copy

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
        
PALETTE_TILE_SIZE = 24

char_list = [' ']

import ctypes
c_uint16 = ctypes.c_uint16
c_uint8 = ctypes.c_uint8
c_ulonglong = ctypes.c_uint64
c_int16 = ctypes.c_int16

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

class PhotoImage_Ex(tk.PhotoImage):

    def transparency_set(self, x, y, boolean):
        #from https://github.com/python/cpython/commit/50866e9ed3e4e0ebb60c20c3483a8df424c02722
        """Set the transparency of the pixel at x,y."""
        self.tk.call(self.name, 'transparency', 'set', x, y, boolean)

class SpriteFields( ctypes.LittleEndianStructure ):
    _fields_ = [
        #("u3",          c_ulonglong,7),
        #("xpos",        c_ulonglong,9),
        ("xpos",        c_ulonglong,16), #i will regret this someday
        
        ("address",     c_ulonglong, 11 ),
        ("xflip",       c_ulonglong, 1 ),
        ("yflip",       c_ulonglong, 1 ),
        ("palette",     c_ulonglong, 2 ),
        ("priority",    c_ulonglong, 1 ),
        
        ("link",        c_ulonglong,7),
        ("u3",          c_ulonglong,1),
        ("height",       c_ulonglong,2),
        ("width",       c_ulonglong,2),
        ("u2",          c_ulonglong,4),
        
        #("u1",          c_ulonglong,6),
        #("ypos",        c_ulonglong,10),
        ("ypos",        c_ulonglong,16),
        ]
        
def decode_s3_sprite(sprite):
    #PCCY XAAA AAAA AAAA
    #      YY 0S VV VV XX XX
    #YY YY 0S LL VV VV XX XX
    pieces = []
    for i in sprite:
        pieces.append(SpriteIndex())
        new_piece = (i & (0xFFFF << 32)) << 8
        new_piece = new_piece | (i & 0xFFFFFFFF)
        pieces[-1].asLongLong = new_piece
        if pieces[-1].ypos > 127:
            pieces[-1].ypos = pieces[-1].ypos | 0xFF00
    return(pieces)

class SpriteIndex( ctypes.Union ):
    _anonymous_ = ("field",)
    _fields_ = [
        ("field",    SpriteFields ),
        ("asLongLong", c_ulonglong    )
        ]

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
        self.variants = {(0,1): tile_to_ppm(self.int_tile, 0, self.palette, output_image = True)}
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
                img = tile_to_ppm(self.transform(xflip, yflip), paletteline, self.palette, output_image = True)
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
                    self.variants[flags,zoom].transparency_set(out_x,out_y,not bool(colour))
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
    
def tile_to_ppm(tile, paletteline, palette, output_image = False, *args):
    ppm = bytearray()
    palettelineoffset = paletteline << 6 #16 * 4
    if tile == None or (None in args):
        ppm = error_ppm
        if output_image:
            image = PhotoImage_Ex(width=8, height=8, data=ppm, format='PPM')
            return(image)
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
        if output_image:
            image = PhotoImage_Ex(width=8, height=8, data=ppm, format='PPM')
            for y in range(tile_height):
                for x in range(8):
                    i = (y << 3) + x
                    if not bool(tile[i]):
                        image.transparency_set(x,y,True)
            return(image)
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
        
class SpriteMapRenderer:
    def __init__(self, canvas, palette, tilelist, zoom):
        self.tilelist = tilelist
        self.canvas = canvas
        self.pieces = []
        self.map = None
        self.x = 0
        self.y = 0
        self.rendered = False
        self.palette = palette
        self.images = []
        self.zoom = zoom
        
    def config(self, x = None, y = None, map = None):
        if map:
            self.set_sprite(map)
        elif not self.map:
            return()
        if x or y:
            self.set_position(x, y)
        else:
            self.render()
        
    def set_sprite(self, map):
        self.map = map
        for piece in self.pieces:
            self.canvas.delete(piece)
        self.sprite_indices = []
        self.pieces = []
        for piece in self.map:
            self.sprite_indices.append(piece)
            
    def insert(self, index, piece):
        self.sprite_indices.insert(index, piece)
        self.render()
        
    def delete(self, index = None):
        if index:
            del self.sprite_indices[index]
        else:
            self.sprite_indices = []
        self.render()
    
    def set_position(self, x, y):
        if not self.rendered:
            self.render()
        for piece in self.pieces:
            vector_x = x - self.x
            vector_y = y - self.y
            cur_coords = self.canvas.coords(piece)
            cur_x = cur_coords[0]
            cur_y = cur_coords[1]
            self.canvas.move(piece, vector_x, vector_y)
        self.x, self.y = x, y
        
    def move_piece(self, index, x, y):
        piece = sel.sprite_indices[index]
        for i in range(2):
            #YY YY 0S LL VV VV XX XX
            coord_value = [piece.xpos, piece.ypos][i]
            vector = [x, y][i]
            coord_value = (coord_value + vector) % 65536
            if i:
                piece.ypos = coord_value
            else:
                piece.xpos = coord_value
        self.canvas.move(self.pieces[index], x, y)
        
    def set_piece_palette(self, index, paletteline):
        self.sprite_indices[index].palette = paletteline
        self.render()
    
    def render(self):
        if not self.map:
            return()
        for piece in self.pieces:
            self.canvas.delete(piece)
        self.pieces = []
        self.images = []
        for piece in self.sprite_indices:
            xpos = piece.xpos
            ypos = piece.ypos
            if xpos > 32767:
                xpos = xpos - 65536
            if ypos > 32767:
                ypos = ypos - 65536
            xpos, ypos = xpos * self.zoom, ypos * self.zoom
            self.pieces.append(self.canvas.create_image(self.x + xpos, self.y + ypos, anchor = tk.NW))
            self.images.append(self.build_piece_ppm(piece))
            self.canvas.itemconfigure(self.pieces[-1], image = self.images[-1])
        self.rendered = True
        
    def build_piece_ppm(self, piece):
        ppm = bytearray()
        height = piece.height + 1
        width = piece.width + 1
        mask = bytearray()
        for y in range(height):
            address_y = y + piece.address
            tiles = []
            for x in range(width):
                try:
                    tiles.append(self.tilelist[address_y + (x * height)])
                except IndexError:
                    tiles.append(None)
            for row in range(8):
                y_offset = row * 8
                for x in range(width):
                    try:
                        tile = tiles[x].int_tile
                        for column in range(8):
                            i = column + y_offset
                            pixel_value = tile[i]
                            r, g, b = self.palette.get_true_rgb_colour(app.paletteline.get() + piece.palette, pixel_value)
                            ppm.append(r)
                            ppm.append(g)
                            ppm.append(b)
                            if pixel_value:
                                mask.append(1)
                            else:
                                mask.append(0)
                    except:
                        for i in range(24):
                            ppm.append(0)
                        for i in range(8):
                            mask.append(1)
        
        header = b'P6 '
        header = header + str(width * 8).encode('ascii')
        header = header + b' '
        header = header + str(height * 8).encode('ascii')
        header = header +  b' 255 '
                            
        ppm = header + ppm
        image = PhotoImage_Ex(data=ppm, format='PPM')
        for y in range(height * 8):
            big_width = width * 8
            y_offset = y * (big_width)
            for x in range(big_width):
                if not mask[y_offset + x]:
                    image.transparency_set(x,y,True)
        image = image.zoom(self.zoom,self.zoom)
        return(image)
        
class SpriteMapEditor(tk.Canvas):
    
    def __init__(self, parent, tilelist, palette, *args, **options):
        tk.Canvas.__init__(self, parent, *args, **options)
        self.config(width = 40*8, height = 28*8, background = 'black')
        self.palette = palette
        self.tilelist = tilelist
        self.sprite = SpriteMapRenderer(self, self.palette, self.tilelist, 2)
            
class ScrolledFrame(tk.Frame):
    """A pure Tkinter scrollable frame that actually works!
    * Use the 'interior' attribute to place widgets inside the scrollable frame
    * Construct and pack/place/grid normally

    """
    def __init__(self, parent, horizontalscroll = False, verticalscroll = True, defaultscroll = 'v', canvas_width = None, canvas_height = None, *args, **kw):
        tk.Frame.__init__(self, parent, *args, **kw)            

        # create a canvas object and a vertical scrollbar for scrolling it
        self.vscrollbar = tk.Scrollbar(self, orient=tk.VERTICAL)
        self.hscrollbar = tk.Scrollbar(self, orient=tk.HORIZONTAL)
        self.canvas = tk.Canvas(self, bd=0, background = '#FFFFFF', highlightthickness=0,
                        yscrollcommand=lambda *args: self.vscrollbar.set(*args), xscrollcommand=lambda *args: self.hscrollbar.set(*args))
        self.canvas.grid(column = 0, row = 0, sticky = 'nsew')
        
        if horizontalscroll:
            self.hscrollbar.grid(row = 1, column = 0, sticky = 'nsew')
            self.hscrollbar.config(command=self.canvas.xview)
            
        if verticalscroll:
            self.vscrollbar.grid(column = 1, row = 0, sticky = 'nsew')
            self.vscrollbar.config(command=self.canvas.yview)

        # reset the view
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)

        # create a frame inside the canvas which will be scrolled with it
        self.interior = tk.Frame(self.canvas)
        self.interior_id = self.canvas.create_window(0, 0, window=self.interior,
                                           anchor=tk.NW)
        
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        if canvas_width != None:
            self.canvas.config(width = canvas_width)
            
        if canvas_height != None:
            self.canvas.config(height = canvas_height)
        
        # track changes to the canvas and frame width and sync them,
        # also updating the scrollbar
        def _configure_interior(event):
            # update the scrollbars to match the size of the inner frame
            self.canvas.config(scrollregion=self.canvas.bbox("all"))
            if self.canvas_width == None:
                if self.interior.winfo_reqwidth() != self.canvas.winfo_width():
                    # update the canvas's width to fit the inner frame
                    self.canvas.config(width=self.interior.winfo_reqwidth())
        self.interior.bind('<Configure>', _configure_interior)
        
        def _bound_to_mousewheel(event):
            self.canvas.bind_all("<MouseWheel>", _on_mousewheel)   

        def _unbound_to_mousewheel(event):
            self.canvas.unbind_all("<MouseWheel>") 

        def _on_mousewheel(event):
            s = event.state
            # Manual way to get the modifiers
            ctrl  = (s & 0x4) != 0
            if (ctrl ^ (defaultscroll != 'v')) and horizontalscroll:
                self.canvas.xview_scroll(int(-1*(event.delta/120)), "units")
            elif ((not ctrl) ^ (defaultscroll != 'v')) and verticalscroll:
                self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        self.bind('<Enter>', _bound_to_mousewheel)
        self.bind('<Leave>', _unbound_to_mousewheel)

            
class TileBrowser(ScrolledFrame):
    def __init__(self, parent, tilelist, var_tile, var_paletteline, *args, **options):
        ScrolledFrame.__init__(self, parent, canvas_width = 8*16)
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
        self.viewer_portal = ScrolledFrame(self, canvas_height = 28*16, canvas_width = 40*16, horizontalscroll = True)
        self.viewer_portal.grid(column = 1, row = 0, rowspan = 2, sticky='nsew')
        self.viewer = MapViewer(self.viewer_portal.interior, self.plane_map_width.get(), self.plane_map_height.get(), self.tilelist, self.planes, height = self.plane_map_height.get()*16, width = self.plane_map_width.get()*16, bd=0, highlightthickness = 0)
        self.viewer.grid()
        self.viewer.config(background = self.palette.get_true_tk_colour(0,0))
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
        
        self.chk_priority = tk.Checkbutton(control_frame, text = "Priority", variable = self.priority)
        self.chk_priority.grid(columnspan = 2)
        
        self.chk_xflip = tk.Checkbutton(control_frame, text = "X flip", variable = self.xflip)
        self.chk_xflip.grid(columnspan = 2)
        self.chk_yflip = tk.Checkbutton(control_frame, text = "Y flip", variable = self.yflip)
        self.chk_yflip.grid(columnspan = 2)
        self.deeptiles = {}
        self.caret_tile = None
        self.caret_pos = None
    

        caret_ppm = array.array('B')
        for i in range(len(caret_mask)):
            for n in range(3):
                caret_ppm.append([0,0,255][caret_mask[i]])
                
        caret_ppm = PPM_HEADER + caret_ppm
                
        self.caret_image = PhotoImage_Ex(width=8, height=8, data=caret_ppm, format='PPM')

        for y in range(8):
            y_offset = y * 8
            for x in range(8):
                if not caret_mask[y_offset + x]:
                    self.caret_image.transparency_set(x,y,True)
                    
        self.caret_image = self.caret_image.zoom(2,2)
                    
        self.caret = self.viewer.create_image(0,0, anchor = tk.NW)
        self.viewer.itemconfigure(self.caret, image = self.caret_image, state = 'hidden')
        self.viewer.tag_raise(self.caret)
        
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
        self.viewer.refresh(x, y, self.selection.get())
        self.viewer.config(background = self.palette.get_true_tk_colour(0,0))
        if self.tool and self.caret_pos:
            y = self.caret_pos[0]
            x = self.caret_pos[1]
            cur_coords = self.viewer.coords(self.caret)
            cur_x = cur_coords[0]
            cur_y = cur_coords[1]
            self.viewer.move(self.caret, (x * 16) - cur_x, (y * 16) - cur_y)
            self.viewer.itemconfigure(self.caret, state = 'normal')
            self.viewer.tag_raise(self.caret)
        else:
            self.viewer.itemconfigure(self.caret, state = 'hidden')
        
class MapViewer(tk.Canvas):
    
    def __init__(self, parent, width_t, height_t, tilelist, planes, *args, **options):
        tk.Canvas.__init__(self, parent, *args, **options)
        self.tilelist = tilelist
        
        self.width_t = width_t
        self.height_t   = height_t
        
        self.config(background = 'black')
        
        self.tiles = [[],[]]
        for y in range(self.height_t):
            for x in range(self.width_t):
                for i in [1,0]:
                    tile = self.create_image(x*16,y*16, anchor = tk.NW)
                    self.tiles[i].append(tile)
            
        self.error_image = tkinter.PhotoImage(width=8, height=8, data=error_ppm, format='PPM')
        self.error_image = self.error_image.zoom(2,2)
        self.planes = planes
            
    def refresh(self, x, y, plane): #PCCY XAAA AAAA AAAA
        if not x:
            if plane > 1:
                self.refresh(None, None, 1)
            for y in range(self.height_t):
                y_offset = y * self.width_t
                for x in range(self.width_t):
                    offset = x + y_offset
                    self.refresh_2(offset, plane)
        else:
            offset = x + (y * self.width_t)
            self.refresh_2(offset, plane)
                
    def refresh_2(self, offset, plane):
        thistile = self.planes[plane % 2][offset]
        tileflags = (thistile.asWord >> 11) & 0b11111
        try:
            self.itemconfigure(self.tiles[plane % 2][offset], image = self.tilelist[thistile.address].variant(tileflags, 2), state='normal')
        except IndexError:
            self.itemconfigure(self.tiles[plane % 2][offset], image = self.error_image, state='normal')
        self.itemconfigure(self.tiles[(plane % 2)^1][offset], state=['hidden', 'normal'][plane > 1])
        #priority = self.planes[0][offset].priority - self.planes[1][offset].priority
        if self.planes[1][offset].priority > self.planes[0][offset].priority:
            self.tag_lower(self.tiles[0][offset])
        else:
            self.tag_raise(self.tiles[0][offset])
        
    def change_size(self, width, height):
        self.width_t = width
        self.height_t = height
        self.config(width = width * 16, height = height * 16)
        for i in [1,0]:
            x = 0
            y = 0
            count = 0
            for tile in self.tiles[i]:
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
                for plane in [1,0]:
                    tile = self.create_image(x*16,y*16, anchor = tk.NW)
                    self.tiles[plane].append(tile)
                x = (x + 1) % width
                if x == 0:
                    y = y + 1
        elif new_tiles < 0:
            for i in range(new_tiles):
                for plane in [1,0]:
                    self.delete(self.tiles[plane][-1])
                    del self.tiles[plane][-1]
            
        for offset in range(len(self.tiles[0])):
            priority = self.planes[0][offset].priority - self.planes[1][offset].priority
            if priority < 0:
                self.tag_lower(self.tiles[0][offset])
            else:
                self.tag_raise(self.tiles[0][offset])

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
        self.selector.config(values = tile_choices)
        self.remove_tile.config(state = tk.NORMAL)
        
        root.event_generate('<<TilesChanged>>')
        
    def remove_tile(self):
        del self.tilelist[self.selection.get()]
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
        
        self.selected_frame = tk.IntVar()
        
        self.plane_map_height = tk.IntVar()
        self.plane_map_height.set(28)
        
        self.menubar = tk.Menu(self.frame)

        self.filemenu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label='File', menu=self.filemenu)
        self.frame.master.config(menu=self.menubar)
        
        self.filemenu.add_command(label='Open sprite...', command=self.open_s3_sprite)
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
        self.frames = []
        
        self.selected_piece = tk.IntVar()

        for y in range(self.plane_map_height.get()):
            for x in range(self.plane_map_width.get()):
                self.map.append(VDPIndex())
                self.map[-1].yflip = y & 1
                self.map[-1].address = x & 1

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
        
        self.nb = ttk.Notebook(self.frame)
        self.map_editor_frm = tk.Frame(self.nb)
        self.sprite_editor_frm = tk.Frame(self.nb)
        
        self.sprite_browser_frm = ScrolledFrame(self.sprite_editor_frm)
        
        self.sprite_browser = tk.Canvas(self.sprite_browser_frm.interior, background = 'black', width = 64)
        
        self.piece_browser_frm = ScrolledFrame(self.sprite_editor_frm)
        
        self.piece_browser = tk.Canvas(self.piece_browser_frm.interior, background = 'grey', width = 288)
        self.piece_browser.pack(side=tk.LEFT, fill = tk.BOTH)
        
        for bind in ["<ButtonPress-1>", "<B1-Motion>"]:
            self.sprite_browser.bind(bind, lambda event: self.frame_clicked(event))
        self.sprite_browser.pack(side=tk.LEFT, fill = tk.Y)
        
        self.sprite_tool = tk.IntVar()
        
        self.sprite_select_rad = tk.Radiobutton(self.sprite_editor_frm, variable = self.sprite_tool, value = 0, text = "Select", indicatoron = 0)
        self.sprite_pixel_rad = tk.Radiobutton(self.sprite_editor_frm, variable = self.sprite_tool, value = 1, text = "Draw", indicatoron = 0)
        
        self.paletteline.trace('w',self.palettelinechanged)
        
        self.tile_editor_frm = tk.Frame(self.map_editor_frm)
        self.tile_editor = TileEditor(self.tile_editor_frm, self.tile, self.tilelist, self.tile, self.paletteline, self.colour)
        
        self.font_tool = FontTool(self.tile_editor_frm, self.tilelist, self.paletteline, self.tile)
        
        self.map_editor = PlaneMapEditor(self.map_editor_frm, self.selected_map, self.palette, self.tilelist, self.tile, self.paletteline, self.planes, self.plane_map_width, self.plane_map_height)
        self.sprite_editor = SpriteMapEditor(self.sprite_editor_frm, self.tilelist, self.palette)
        self.nb.add(self.map_editor_frm, text = "Planemap Editor")
        self.nb.add(self.sprite_editor_frm, text = "Sprite Editor")
        self.nb.pack(side=tk.LEFT, fill = tk.BOTH)
        self.sprite_editor.pack(side=tk.LEFT, fill = tk.BOTH)
        self.piece_browser_frm.pack(side=tk.LEFT, fill = tk.BOTH)
        self.sprite_browser_frm.pack(side=tk.LEFT, fill = tk.BOTH)
        
        tk.Label(self.sprite_editor_frm, text = "Tool:").pack(side=tk.LEFT, anchor = "n")
        self.sprite_select_rad.pack(side=tk.LEFT, anchor = "n")
        self.sprite_pixel_rad.pack(side=tk.LEFT, anchor = "n")
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
        
        self.pieces = []
        
        
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
        
    def frame_clicked(self, event):
        x, y = event2canvas(event, self.sprite_browser)
        y = int(y) >> 6
        
        self.selected_frame.set(y)
        
        self.sprite_editor.sprite.config(map = self.frame_indices[y])
        
        self.render_pieces()
        
        
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
        self.map_editor.refresh()
        
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
            
    def open_s3_sprite(self):
        filename = tk.filedialog.askopenfilename(title = "Open sprite", filetypes = (("BIN files","*.bin"),("all files","*.*")))
        if filename !='':
            #pieces = []
            with open(filename, 'rb') as binary_file:
                data = binary_file.read()
            i = 0
            frames = []
            while i < len(data):
                piece_count = (data[i] << 8) + data[i + 1]
                pieces = []
                i = i + 2
                for piece in range(piece_count):
                    thispiece = 0
                    for j in range(6):
                        thispiece = thispiece << 8
                        thispiece = thispiece + data[i+j]
                    i = i + 6
                    pieces.append(thispiece)
                frames.append(decode_s3_sprite(pieces))
            self.sprite_browser.config(height = len(frames) * 64)
            for frame in self.frames:
                frame.delete()
            self.frames = []
            i = 0
            for frame in frames:
                self.frames.append(SpriteMapRenderer(self.sprite_browser, self.palette, self.tilelist, 1))
                self.frames[-1].config(map = frame, x = 32, y = (64 * i) + 32)
                i = i + 1
                
            self.frame_indices = frames

            #for i in range(0,len(data) - 1, 6):
            #    thispiece = 0
            #    for j in range(6):
            #        thispiece = thispiece << 8
            #        thispiece = thispiece + data[i+j]
            #    pieces.append(thispiece)
        self.selected_frame.set(0)
        self.sprite_editor.sprite.config(map = frames[0], x = 8*32, y = 8*32)
        self.render_pieces()
        
    def render_pieces(self):
        y = 0 #width = 288
        for i in self.pieces:
            i.delete()
        for i in self.frame_indices[self.selected_frame.get()]:
            if i.width > i.height:
                max = i.width
            else:
                max = i.height
            zoom = [36,18,12,9][max]
            height = (zoom * (i.height + 1) * 8) + 72
            self.pieces.append(SpriteMapRenderer(self.piece_browser, self.palette, self.tilelist, zoom))
            map = copy.deepcopy(i)
            map.xpos = 0
            map.ypos = 0
            self.pieces[-1].config(x = 0, y = y, map = [map])
            y = y + height
        self.piece_browser.config(height = y - 72)
            
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
        filename = tk.filedialog.askopenfilename(title = "Open palette",filetypes = (("BIN files","*.bin"),("all files","*.*")))
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
        self.tile_editor.viewer.config(background = self.palette.get_true_tk_colour(0,0))
        for i in self.tile_browser.tiles:
            i.config(background = self.palette.get_true_tk_colour(0,0))
        
    def put_pixel(self):
        self.tile_editor.refresh()
        
    def last_pixel(self):
        self.map_editor.refresh()
        self.tile_browser.refresh()
        self.font_tool.refresh()
        
    def palettelinechanged(self, *args):
        for frame in self.frames:
            frame.render()

root = tk.Tk()

app = App(root)

app.palette_tool.refresh()

app.tile_browser.refresh()
    
app.map_editor.refresh()

app.tile_editor.refresh()

root.mainloop()