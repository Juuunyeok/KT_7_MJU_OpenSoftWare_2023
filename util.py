"""
util.py:
This is an integrated toolkit module for mygame, provides many useful functions and objects,
such as UI components: buttons, panels, text boxes; and many other game-render helpers.
It is recommended to import selected items from this module, rather than importing all.
"""
import pygame
import math
from database import REC_DATA


# ====================================================
# A more advanced BASIC Sprite class for this game, with lift() & level().
class InanimSprite(pygame.sprite.Sprite):
    def __init__(self, category):
        pygame.sprite.Sprite.__init__(self)
        self.category = category
    
    def paint(self, surface):
        surface.blit(self.image, self.rect)

    def lift(self, dist):
        self.rect.bottom += dist
    
    def level(self, dist):
        self.rect.left += dist


# ====================================================
# Basic UI gadgets.
# 富文本（图片+文字混合）对象
class RichText():
    def __init__(self, content, img, font, line_width=200):
        # tag '_IMG_' in the content shows the place to put img.
        self.original_text = content
        self.text_lines = []
        self.surface_lines = []
        self.font = font
        self.surf = [ self.arrange_text(content[i], img, font[i]) for i in range(len(content)) ]
        self.rect = [ each.get_rect() for each in self.surf ]

    def arrange_text(self, line, img, font):
        """
        docstring
        """
        # 1. rescale image to fit line height
        line_h = font.size( line )[1]
        if img.get_height()>line_h:
            ratio = line_h/img.get_height()
            img = pygame.transform.smoothscale(img, (round(img.get_width()*ratio), line_h))
        # 2. compute the space for img
        img_width = img.get_width()
        space = ""
        while font.size( space )[0]<img_width:
            space += " "
        line = line.replace("_IMG_", space)
        # 3. create the txt surface
        surface = font.render( line, True, (255,255,255) )
        # 4. find pos and place image
        char_width = [ tup[-1] for tup in font.metrics(line) ]
        img_index = [ indx+1 for indx in self.find_all(space, line) ]   # +1 to avoid zero
        for each in img_index:
            left_offset = sum(char_width[:each])
            surface.blit(img, (left_offset, 0))
        
        return surface
        #print(font.metrics(line))
        #print(font.size(line))
        
    def find_all(self, sub, s):
        index_list = []
        index = s.find(sub)
        while index != -1:
            index_list.append(index)
            # unrepeated finding. if allow repeating: set +len(sub) as +1
            index = s.find(sub,index+len(sub))
        
        return index_list
    
    def paint(self, screen, x, y):
        lgg = REC_DATA["SYS_SET"]["LGG"]
        self.rect[lgg].left = x - self.rect[lgg].width//2
        self.rect[lgg].top = y - self.rect[lgg].height//2
        screen.blit( self.surf[lgg], self.rect[lgg] )

    def truncate(self, content, font, line_width):
        for i in range(2):
            # 1. cut the original text into chunks
            self.text_lines.append( [] )
            text = content[i]
            start = 0
            offset = 1
            while start+offset<len(text):
                if font[i].size( text[start:start+offset] )[0]>= line_width:
                    self.text_lines[i].append(text[start:start+offset])
                    start = start + offset
                    offset = 1
                else:
                    offset += 1
            # process the possible residual
            if offset>1:
                self.text_lines[i].append(text[start:start+offset])
            # 2. for each in text_lines, form a surface
            self.surface_lines.append( [] )
            for line in self.text_lines[i]:
                self.surface_lines[i].append(
                    font[ REC_DATA["SYS_SET"]["LGG"] ].render(line, True, (255,255,255))
                )

# 图片按钮对象
class ImgButton():
    def __init__(self, img_dic, init_key, font, labelPos="ctr"):
        '''labelPos: ctr, top, or btm.'''
        self.key = init_key
        self.font = font
        self.labelPos = labelPos
        # 1-Draw Img.
        self.imgList = img_dic
        self.image = self.imgList[self.key]
        self.rect = self.image.get_rect()
        # 2-Make highlight.
        self.shadList = {}
        for key in self.imgList:
            shad = self.imgList[key].copy()
            shad.lock()
            for x in range(shad.get_width()):
                for y in range(shad.get_height()):
                    if shad.get_at((x,y))[3]>0:
                        shad.set_at( (x,y), (240,240,240,80) )
            shad.unlock()
            self.shadList[key] = shad

    def _setPos(self, x, y):
        self.rect.left = x - self.rect.width//2
        self.rect.top = y - self.rect.height//2

    def changeKey(self, key):
        self.key = key
        self.image = self.imgList[self.key]
        self.rect = self.image.get_rect()

    def hover_on(self, pos):
        if ( self.rect.left < pos[0] < self.rect.right ) and ( self.rect.top < pos[1] < self.rect.bottom ):
            return True
        return False

    def paint(self, screen, x, y, pos, label=()):
        self._setPos(x, y)
        screen.blit( self.image, self.rect )
        if self.hover_on(pos):
            # paint shad & label
            screen.blit( self.shadList[self.key], self.rect )
            if label:
                txt = self.font[ REC_DATA["SYS_SET"]["LGG"] ].render(label[ REC_DATA["SYS_SET"]["LGG"] ], True, (255,255,255))
                rect = txt.get_rect()
                rect.left = x - rect.width//2
                if self.labelPos=="ctr":
                    rect.top = y - rect.height//2
                elif self.labelPos=="top":
                    rect.top = y - rect.height//2 - 40
                elif self.labelPos=="btm":
                    rect.top = y - rect.height//2 + 40
                screen.blit( txt, rect )
        return self.rect

# 文本按钮对象
class TextButton():
    def __init__(self, w, h, label_dic, init_key, font, rgba=(20,20,20,180)):
        # 1-Draw Rect.
        self.surf = pygame.Surface( (w,h) ).convert_alpha() # 实际显示的surface对象，带有标签和装饰
        self.surf.fill((0,0,0,0))
        self.rect = self.surf.get_rect()
        self.surf.blit( rounded_surf( (w,h), rgba), self.rect )
        self.surf_ori = self.surf.copy()    # 原始surface对象（文字可能变化）
        
        # 2-Draw Txt.
        self.label_dic = label_dic
        self.label = self.label_dic[init_key]
        self.font = font
        self.txt_ctr = [w//2, h//2]
        self.draw_text()
        # 3-highlight cover.
        self.hover_surf = rounded_surf( (w-8, h-8), (210,210,210,60), r=5 ) # 当悬停时要覆盖的高亮层

    def draw_text(self, label_key="NULL"):
        '''由于按钮的标签会受到设置语言改变，故单独设置一个函数以便动态更改'''
        lgg = REC_DATA["SYS_SET"]["LGG"]
        if label_key!="NULL":
            self.label = self.label_dic[label_key]
        txt = self.font[lgg].render(self.label[lgg], True, (255,255,255))
        rect = txt.get_rect()
        rect.left = self.txt_ctr[0] - rect.width//2
        rect.top = self.txt_ctr[1] - rect.height//2
        self.surf = self.surf_ori.copy()
        self.surf.blit( txt, rect )

    def _setPos(self, x, y):
        self.rect.left = x - self.rect.width//2
        self.rect.top = y - self.rect.height//2

    def hover_on(self, pos):
        if ( self.rect.left < pos[0] < self.rect.right ) and ( self.rect.top < pos[1] < self.rect.bottom ):
            return True
        return False

    def paint(self, screen, x, y, pos):
        # paint button.
        self._setPos( x, y )
        screen.blit( self.surf, self.rect )
        # paint bg if hovered on.
        if self.hover_on(pos):
            rect = self.hover_surf.get_rect()
            rect.left = self.rect.left+4
            rect.top = self.rect.top+4
            screen.blit( self.hover_surf, rect )
        return self.rect

# 复合按钮对象
class RichButton(TextButton):
    def __init__(self, w, h, img, label_dic, init_key, font, rgba=(20,20,20,180), align='vertical'):
        '''labelDic: {key1: ("eng","中文"), key2: ("eng","中文")}.
            align: vertical or horizontal.'''
        TextButton.__init__(self, w, h, label_dic, init_key, font, rgba=rgba)
        if align=='vertical':
            img_ctr = [w//2, h*0.4]
            self.txt_ctr = [w//2, h*0.8]
        elif align=='horizontal':
            img_ctr = [w*0.2, h//2]
            self.txt_ctr = [w*0.65, h//2]
        # 1-Draw Rect.
        self.surf = pygame.Surface( (w,h) ).convert_alpha()
        self.rect = self.surf.get_rect()
        self.surf.fill( (0,0,0,0) )
        self.surf.blit( rounded_surf( (w,h), rgba), self.rect )
        # 2-Draw Img.
        rect = img.get_rect()
        rect.left = img_ctr[0] - rect.width//2
        rect.top = img_ctr[1] - rect.height//2
        self.surf.blit( img, rect )
        self.surf_ori = self.surf.copy()
        # 3-Draw Txt.
        self.label_dic = label_dic
        self.label = self.label_dic[init_key]
        self.font = font
        self.draw_text()
        # 4-Other dec.
        self.hover_surf = rounded_surf( (w-8, h-8), (240,240,240,40), r=5 )
        self.prompt_surf = rounded_surf( (w, 20), (20,240,20,140) )
        self.prompt_info = []

    def add_prompt(self, text):
        self.prompt_info = [text, REC_DATA["SYS_SET"]["LGG"]]
    
    def paint(self, screen, x, y, pos):
        # paint button.
        self._setPos(x, y)
        screen.blit( self.surf, self.rect )
        # paint bg if hovered on.
        if self.hover_on(pos):
            rect = self.hover_surf.get_rect()
            rect.left = self.rect.left+4
            rect.top = self.rect.top+4
            screen.blit( self.hover_surf, rect )
        if self.prompt_info:
            # BG.
            rect = self.prompt_surf.get_rect()
            rect.left = self.rect.left
            rect.top = self.rect.top
            screen.blit( self.prompt_surf, rect )
            # TEXT.
            txt = self.font[self.prompt_info[1]].render(self.prompt_info[0][self.prompt_info[1]], True, (255,255,255))
            rect = txt.get_rect()
            rect.left = self.rect.left + self.rect.width//2 - rect.width//2
            rect.top = self.rect.top
            screen.blit( txt, rect )
            self.prompt_info.clear()
        return self.rect

# 小面板挂件（可以装载各种按钮对象、文本和图片）
class Panel():
    def __init__(self, w, h, font, title=(), rgba=(10,10,10,150), imgH=90, align="center"):
        '''
        'align' could be center or left.
        '''
        self.surf_orig = rounded_surf( (w,h), rgba ) # 实际显示的surface对象
        self.surf = self.surf_orig.copy()
        self.bgColor = rgba
        self.rect = self.surf.get_rect()
        self.font = font
        self.items = []
        # imgH: each image will have to occupy this height.
        self.imgH = imgH
        self.align = align
        if self.align=="center":
            self.x = self.rect.width//2
            self.offset = True
        elif self.align=="left":
            self.x = self.rect.width//20
            self.offset = False
        else:
            raise ValueError("align can only be center or left!")
        # Title.
        self.title = title
        self.titleSurf = rounded_surf( (w,24), (255,255,255,200), r=5 )
        self.titleRect = self.titleSurf.get_rect()
        self.titleRect.left = self.titleRect.top = 0

    def addItem(self, item, tag=None, inline=False):
        '''item could be:
            Button Objects: TextButton, RichButton (exclude ImgButton); 
            String tuples: (txt1, txt2), [txt1, txt2];
            RichText Objects;
            Surfaces (images).
            'tag' is suggested when item is a Button.
            'inline' means this item should try to be in the same line with the previous item. Currently only valid for Button.
        '''
        if type(item) in [tuple, list]:
            tp = "Text"
        elif type(item) == RichText:
            tp = "RichText"
        elif type(item) in [TextButton, RichButton]:
            tp = "Button"
            item.tag = tag
        elif type(item) == pygame.Surface:
            tp = "Image"
            if item.get_height()>self.imgH: # if is image: scale into self.imgH
                item = pygame.transform.smoothscale( item, (item.get_width()*self.imgH/item.get_height(),self.imgH) )
        else:
            return False
        self.items.append( {"item": item, "type": tp, "inline": inline,} )
        return self
    
    def updateButton(self, but_tag=None, label_key="NULL"):
        if not but_tag:     # update all (lgg)
            for item in self.items:
                if item["type"] == "Button":
                    item["item"].draw_text("NULL")
        else:               # update specific button (label)
            for item in self.items:
                if item["type"] == "Button" and item["item"].tag==but_tag:
                    item["item"].draw_text(label_key)

    def updateText(self, index, new_content):
        if index<len(self.items) and self.items[index]["type"] in ["Text", "RichText"]:
            self.items[index]["item"] = new_content
        else:
            raise ValueError("Index out of range or try to update text on a button!")

    def _setPos(self, x, y):
        self.rect.left = x - self.rect.width//2
        self.rect.top = y - self.rect.height//2
        
    def paint(self, screen, x, y, pos):
        '''cursor pos will be set to fit offset in this function'''
        self._setPos(x, y)
        self.surf = self.surf_orig.copy()
        pos = (pos[0]-x+self.rect.width//2, pos[1]-y+self.rect.height//2)
        in_y = 5
        lgg = REC_DATA["SYS_SET"]["LGG"]
        # Paint title if Panel got one.
        if self.title:
            # Title BG.
            self.surf.blit(self.titleSurf, self.titleRect)
            txt = self.font[lgg].render(self.title[lgg], True, (0,0,0))
            rect = txt.get_rect()
            rect.left = self.rect.width//2 - rect.width//2
            rect.top = in_y
            self.surf.blit( txt, rect )
            in_y += max(rect.height, 24)
        # Pain list items.
        chosenBut = None
        for item in self.items:
            if item["type"]=="Text":
                txt = self.font[lgg].render(item["item"][lgg], True, (255,255,255))
                rect = txt.get_rect()
                rect.left = self.x - rect.width//2 * int(self.offset)
                rect.top = in_y
                self.surf.blit( txt, rect )
                p_rect = rect
                in_y += max(rect.height, 24)
            elif item["type"]=="RichText":
                item["item"].paint(self.surf, self.x + item["item"].rect[lgg].width//2 * int(not self.offset), in_y+item["item"].rect[lgg].height//2)
                in_y += max(item["item"].rect[lgg].height, 24)
                p_rect = item["item"].rect[lgg]
            elif item["type"]=="Button":
                btn = item["item"]
                if item["inline"]:
                    in_y -= (p_rect.height + 4)
                    this_x = p_rect.right + btn.rect.width//2 + 2
                else:
                    this_x = self.x + btn.rect.width//2 * int(not self.offset)
                btn.paint(self.surf, this_x, in_y+btn.rect.height//2, pos)
                in_y += btn.rect.height + 4
                p_rect = btn.rect
                if btn.hover_on(pos):
                    chosenBut = btn
            elif item["type"]=="Image":
                rect = item["item"].get_rect()
                rect.left = self.x - rect.width//2 * int(self.offset)
                rect.top = in_y+ self.imgH//2- rect.height//2
                self.surf.blit(item["item"], rect)
                p_rect = rect
                in_y += self.imgH
        screen.blit(self.surf, self.rect)
        return chosenBut    # 返回被选中的按钮

    def clear(self):
        self.title = ()
        self.items.clear()

# 图片切换效果器
class ImgSwitcher():
    def __init__(self):
        self.SSList = []

    # 为了降低保存图片平滑切换元素的存储开销，添加时进行一系列简单的处理，将起止地址、切换时间转换为增量。
    def addSwitch(self, image, rect, endSize, dx, dy, time=10):  # endSize为以百分数，以1为原大小；dx，dy是相对位移
        if not image or not rect:
            return False
        scaleX = int( (endSize-1)*rect.width//time )  # 尺寸大小的缩放量
        scaleY = int( (endSize-1)*rect.height//time )
        dx = int(dx//time)   # 距离的每次偏移量
        dy = int(dy//time)
        self.SSList.append( [image, rect, (scaleX, scaleY), (dx,dy), time] )

    def doSwitch(self, screen):
        for each in self.SSList:
            newW = each[1].width + each[2][0]
            newH = each[1].height + each[2][1]
            newImg = pygame.transform.smoothscale(each[0], (newW, newH))
            rect = newImg.get_rect()
            newCtr = (each[1].left+each[1].width//2-rect.width//2, each[1].top+each[1].height//2-rect.height//2)
            rect.left = newCtr[0] + each[3][0]
            rect.top = newCtr[1] + each[3][1]
            each[1] = rect
            each[4] -= 1
            screen.blit( newImg, rect )
            if each[4]<=0:
                self.SSList.remove(each)


# ====================================================
# Game helpers: HPBar, message managers, etc.
# 消息管理器
class MsgManager():
    # about message and alerts
    alertDic = { "falseHero":("This Hero is locked.","此英雄尚未解锁。"), 
        "notFound":("Kill one in adventure model to collect.","在冒险模式中击杀一只此怪物来收集它。"), 
        "falseStg":("This Stage is locked.","此关卡尚未解锁。"), 
        "false2P":("You have only one hero accessible.","你目前只有一个可用的英雄。"),
        "illegalKey":("RETURN Key should not be set freely.","回车键不能被设置为玩家按键。"),
        "lackSP":("The hero doesn't have enough SP.","该英雄没有足够的技能点。"),
        "attMax":("This attri is at MAX level.","此项属性已经升至最高级。"),
        "NULL":("An undefined error occurred.","出现了一项未知错误。"),

        "lackGem":("No enough gems!","宝石数量不足！") }
    
    def __init__(self, font, stg, mode="left"):
        self.mode = mode        # could be "left" or "top"
        # 按照消息优先级分为两个框；第一个框为空时优先填入第一个框；第二个框是可以抢占的。
        self.msgList = []       # 等待显示的消息列表。
        self.activeMsg = None   # 当前正在显示的消息。
        self.spareMsg = None    # 备用的消息位置，供紧急消息使用，当active位置被占用时，可以显示在此处。
        # Related resources.
        if self.mode=="left":
            self.card_size = (200,90)
            text_w = 170
        elif self.mode=="top":
            self.card_size = (560,60)
            text_w = 480
        self.frameColor = {"msg":(180,160,160), "dlg":(250,200,160), "item":(130,255,130)}
        self.frameGap = 4
        self.font = font
        self.noticeSnd = pygame.mixer.Sound("audio/notice.wav")
        self.msgStick = { "msg": pygame.image.load("image/tip.png").convert_alpha(), 
            "item": pygame.image.load("image/tip.png").convert_alpha()
        }
        # 若为冒险模式章节还应有对话图标
        if stg>0:
            self.msgStick["dlg"] = pygame.image.load(f"image/stg{stg}/preFig.png").convert_alpha()
        # Decide line volume.
        tmp1 = ""
        while self.font[0].size( tmp1 )[0]<text_w:
            tmp1 += "a"
        tmp2 = ""
        while self.font[1].size( tmp2 )[0]<text_w:
            tmp2 += "我"
        self.vol = [len(tmp1)-1, len(tmp2)-1]
        # 最显目的消息：屏幕中央横条，只有一个位置
        self.ctr_msg = None
        self.ctr_h = 60

    def addMsg(self, content, type="msg", urgent=False, duration=180, icon=None):
        '''
            type: msg, dlg, item or ctr.
            urgent: True- shall blit anyway. if activeMsg is vaccant show there;
                if not show at spareMsg(can override other msg on this place).
                    False- can wait for a vacant activeMsg.
        '''
        if type in  ["msg","dlg","item"]:
            # 1-Make card Rect.
            card = pygame.Surface( self.card_size ).convert_alpha()
            card.fill( (0,0,0,180) )
            cardRect = card.get_rect()
            if self.mode=="left":
                cardRect.right = 0
                cardRect.top = 160
                pygame.draw.rect(card, self.frameColor[type], 
                                (-1, self.frameGap, cardRect.width+1-self.frameGap, cardRect.height-self.frameGap*2), 
                                1)
            elif self.mode=="top":
                cardRect.bottom = 0
                cardRect.left = (960-self.card_size[0]) //2
                pygame.draw.rect(card, self.frameColor[type], 
                                (self.frameGap, -1, cardRect.width-self.frameGap*2, cardRect.height+1-self.frameGap), 
                                1)
            # 2-Draw icon.
            imgRect = self.msgStick[type].get_rect() if not icon else icon.get_rect()
            if self.mode=="left":
                imgRect.left = -20 -imgRect.width//2
                imgRect.top = 180 - imgRect.height//2
            elif self.mode=="top":
                imgRect.left = cardRect.left +30 -imgRect.width//2
                imgRect.top = cardRect.top +cardRect.height//2 -imgRect.height//2
            # 3-Draw Txt. Need to cut long msg into lines.
            if type=="dlg":
                duration = 210
            if type=="item":
                content = (f"Get rare item [{content[0]}]",f"获得稀有物品【{content[1]}】。")
                duration = 150
            lgg = REC_DATA["SYS_SET"]["LGG"]
            string = content[ lgg ]
            y = 10
            while len(string)>0:
                # Render
                txt = self.font[lgg].render( string[0:self.vol[lgg]], True, (255,255,255) )
                rect = txt.get_rect()
                if self.mode=="left":
                    rect.left = 10
                    rect.top = y
                elif self.mode=="top":
                    rect.left = 70
                    rect.top = y
                card.blit( txt, rect )
                # Cut and check more
                string = string[self.vol[lgg]:]
                y += 20
            # 4-wrap
            msgObj = {"card":card, "rect":cardRect, "sticker":self.msgStick[type] if not icon else icon, "stickerRect":imgRect, "cnt":duration, "urgent":urgent}
            self.msgList.append( msgObj )
        elif type=="ctr":
            self.ctr_msg = {"card":None, "rect":None, "text":content, "sticker":icon, "cnt":duration, "show":True, "span":0}
            return None

    def alert(self, title):
        # 供特殊标语使用。警告内容均为urgent。
        self.addMsg(self.alertDic[title], urgent=True)

    def run(self, pause=False):
        # 若active位置为空，则取队列中第一个设为显示
        if self.activeMsg==None and len(self.msgList)>0:
            self.activeMsg = self.msgList[0]
            self.msgList.pop(0)
            self.noticeSnd.play(0)
        # 有正在显示的消息，检查是否需要弹出（暂停时则不移动）
        elif self.activeMsg:# and not pause:
            if self.activeMsg["cnt"]<=0:
                del self.activeMsg
                self.activeMsg = None
            else:
                self.activeMsg["cnt"] -= 1
                # pop card
                if self.mode=="left" and self.activeMsg["rect"].left<0:
                    self.activeMsg["rect"].left = min(self.activeMsg["rect"].left+8, 0)
                    self.activeMsg["stickerRect"].left += 8
                elif self.mode=="top" and self.activeMsg["rect"].top<0:
                    self.activeMsg["rect"].top = min(self.activeMsg["rect"].top+6, 0)
                    self.activeMsg["stickerRect"].top += 6
        # 检查spare消息。spare为空时不主动找消息填，而是等待紧急消息来抢占自己。
        if self.spareMsg and self.mode=="left":# and not pause:
            if self.spareMsg["cnt"]<=0:
                del self.spareMsg
                self.spareMsg = None
            else:
                self.spareMsg["cnt"] -= 1
                # pop card
                if self.mode=="left" and self.spareMsg["rect"].left<0:
                    self.spareMsg["rect"].left = min(self.spareMsg["rect"].left+8, 0)
                    self.spareMsg["stickerRect"].left += 8
        # 以上代码执行后，列表中有两种情况：
        # 若active空，则无消息排队；
        # active满，可能有消息排队。针对此需要检查是否有紧急消息，若有则填补spare位置
        if self.mode=="left":
            for msg in self.msgList:
                if msg["urgent"]==True:
                    if self.spareMsg:
                        del self.spareMsg
                        self.spareMsg = None
                    # 上位
                    self.noticeSnd.play(0)
                    msg["rect"].top += (self.card_size[1]+10)
                    msg["stickerRect"].top += (self.card_size[1]+10)
                    self.spareMsg = msg
                    self.msgList.remove(msg)
                    break
        # Finally: 中心大消息
        if self.ctr_msg:
            if pause:
                self.ctr_msg["show"] = False
            else:
                self.ctr_msg["show"] = True
                self.ctr_msg["span"] += 2
                if self.ctr_msg["span"] >= self.ctr_h:
                    self.ctr_msg["span"] = self.ctr_h
                    self.ctr_msg["cnt"] -= 1
                    if self.ctr_msg["cnt"]<=0:
                        self.ctr_msg = None
    
    def clear(self):
        self.msgList.clear()
        self.activeMsg = None
        self.spareMsg = None
        
    def paint(self, screen):
        if self.activeMsg:
            screen.blit( self.activeMsg["card"], self.activeMsg["rect"] )
            screen.blit( self.activeMsg["sticker"], self.activeMsg["stickerRect"] )
        if self.spareMsg:
            screen.blit( self.spareMsg["card"], self.spareMsg["rect"] )
            screen.blit( self.spareMsg["sticker"], self.spareMsg["stickerRect"] )
        if self.ctr_msg and self.ctr_msg["show"]:
            if self.ctr_msg["span"]<=self.ctr_h:
                card = pygame.Surface( (screen.get_width(), self.ctr_msg["span"]) ).convert_alpha()
                card.fill( (20,20,20,210) )
                cardRect = card.get_rect()
                cardRect.left = 0
                cardRect.top = screen.get_height()//3
                # Render TXT
                txt = self.font[REC_DATA["SYS_SET"]["LGG"]].render( self.ctr_msg["text"][REC_DATA["SYS_SET"]["LGG"]], True, (255,255,255) )
                rect = txt.get_rect()
                rect.left = cardRect.width//2 -rect.width//2
                rect.top = cardRect.height//2 -rect.height//2
                card.blit( txt, rect )
                # Draw icon.
                if self.ctr_msg["sticker"]:
                    imgRect = self.ctr_msg["sticker"].get_rect()
                    imgRect.right = rect.left -10
                    imgRect.top = cardRect.height//2 -imgRect.height//2
                    card.blit( self.ctr_msg["sticker"], imgRect )
                self.ctr_msg["card"], self.ctr_msg["rect"] = card, cardRect
            screen.blit( self.ctr_msg["card"], self.ctr_msg["rect"] )

# 血条管理器
class HPBar():
    iconG = None
    colorSet = {
        #        lightColor          color     shadeColor
        "green": [(120, 250, 120), (0, 210, 0), (0, 160, 0)],
        "lightGreen": [(160, 255, 160), (80, 240, 80), (60, 180, 60)],

        "yellow": [(255, 210, 20), (220, 160, 10), (150, 120, 0)],
        "orange": [(250, 210, 180), (220, 180, 100), (160, 110, 40)],

        "blue": [(150, 160, 250), (60, 80, 210), (10, 30, 160)],

        "red": [(255, 100, 100), (210, 0, 0), (160, 0, 0)],
        "goldRed": [(250, 160, 120), (190, 90, 20), (140, 40, 0)]
    }

    def __init__(self, full, blockVol=100, blockLen=10, gap=1, barOffset=0, barH=8, color="red", icon=False):
        """
            param full: 角色的HP上限
            param blockVol: 每个方格满时表示多少HP
            param blockLen: 每个方格长度至多为多少像素
            param gap: 相邻方格之间的距离
            param barOffset: 绘制时，距离角色的上方偏离
            param barH: 血条高度
            param color: str.血条颜色
        """
        if not HPBar.iconG:
            HPBar.iconG = pygame.transform.smoothscale( pygame.image.load("image/goalie.png").convert_alpha(), (25,24) )
        self.setColor(color)
        self.blockVol = blockVol    # 每个方格满时表示~滴血
        self.blockLen = blockLen    # 每个方格长度至多为~像素
        self.gap = gap
        gapNum = math.ceil( full/self.blockVol )-1  # 格子中间间隔的数量
        self.barLen = full*self.blockLen/self.blockVol + gapNum*self.gap + self.gap*2     # 计算血条总长度+所有gap宽度
        self.barOffset = barOffset  # 血条底端离owner的距离
        # 外边框（白色半透底框）
        self.barH = barH
        self.barBG = pygame.Surface( (self.barLen, self.barH) ).convert_alpha()
        self.barBG.fill( (255,255,255,210) )
        if icon:
            self.iconR = self.iconG.get_rect()
        else:
            self.iconR = None
            
    def paint(self, owner, surface, data="health"):
        if data=="health":
            health = max( owner.health, 0 )
        elif data=="superPower":
            health = min( owner.superPowerCnt, owner.superPowerFull)
        
        x = owner.rect.left+owner.rect.width//2 -self.barLen/2     # 中线减去血条长度的一半
        y = owner.rect.top-self.barH-self.barOffset
        if self.iconR:
            # 画区域守卫的标志
            self.iconR.left = x -self.iconR.width
            self.iconR.top = y -10
            surface.blit( self.iconG, self.iconR )
        # 画外边框
        surface.blit( self.barBG, (x,y) )
        # 画内部血格
        offset = 0             # 用于计算每个方格的偏移值
        while (health > 0):
            w = min(self.blockLen, health*self.blockLen//self.blockVol)     # w是当前的方格的血的宽度，最多为10。
            block = pygame.Rect( x+self.gap+offset, y+self.gap, w, self.barH-self.gap*2 )
            light = pygame.Rect( x+self.gap+offset, block.top, w, self.gap*2 )
            shadow = pygame.Rect( x+self.gap+offset, block.bottom-self.gap*2, w, self.gap*2 )
            pygame.draw.rect( surface, self.color, block )
            pygame.draw.rect( surface, self.lightColor, light )
            pygame.draw.rect( surface, self.shadeColor, shadow )
            health -= self.blockVol
            offset += (self.blockLen+self.gap)
    
    def setColor(self, color):
        self.lightColor, self.color, self.shadeColor = self.colorSet[color]


# ====================================================
# Useful functions, most about Surface processing.
def getPos(sprite, x=0.5, y=0.5):
    '''sprite是要处理的sprite对象，参数x和y都应是[0，1]的数，分别是横坐标和纵坐标相对于整个rect的比例'''
    posX = round( sprite.rect.left + sprite.rect.width*x )
    posY = round( sprite.rect.top + sprite.rect.height*y )
    return [posX, posY]

def drawRect(x, y, width, height, rgba, screen):
    '''常用的画rectangle 的 surface函数'''
    surf = pygame.Surface( (width, height) ).convert_alpha()
    rect = surf.get_rect()
    rect.left = x
    rect.top = y
    surf.fill( rgba )
    screen.blit( surf, rect )
    return rect

def rounded_surf(size, rgba, r=10):
    canv = pygame.Surface( size ).convert_alpha()
    canv.fill( (0,0,0,0) )
    rect = canv.get_rect()
    pygame.draw.rect(canv, rgba, rect, 0, border_radius=r)
    return canv
    
def rot_center(image, angle, subsurf=True):
    """rotate an image while keeping its center and size. NOTE:
    subsurf means if the new image should be limited within original rect"""
    rot_rect = image.get_rect().copy()
    rot_image = pygame.transform.rotate(image, angle)
    rot_rect.center = rot_image.get_rect().center
    if subsurf:
        rot_image = rot_image.subsurface(rot_rect).copy()
    return rot_image

def generateShadow(img, color=(10,10,10,80)):
    '''根据给的单张image转化出阴影并返回'''
    shad = img.copy()
    shad.lock()
    for x in range(shad.get_width()):
        for y in range(shad.get_height()):
            if shad.get_at((x,y))[3]>0:
                shad.set_at( (x,y), color )
    shad.unlock()
    return shad

def getCld(core, group, cateList):
    '''
    Assistant function for many of hero's movement check, stone.fall, etc.
    '''
    spriteList = []
    cldList = pygame.sprite.spritecollide(core, group, False, pygame.sprite.collide_mask)
    for item in cldList:
        if item.category in cateList:
            spriteList.append(item)
    return spriteList