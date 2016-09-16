import re
import json
import lxml.html
import xml.etree.ElementTree as ET

class Parser():

    def __init__(self, doc):
        self.doc = doc

    def parse_to_json(self,pattern, cut_head, cut_tail, DOTALL=False):
        if DOTALL:
            m = re.search(pattern, self.doc, re.DOTALL)
        else:
            m = re.search(pattern, self.doc)
        if m:
            json_section = m.group(0)
            json_section = re.sub(cut_head, '{', json_section) # r'^[^\{]*\{'
            json_section = re.sub(cut_tail, '}', json_section) # r'\};$'
            # parse json
            json_obj = json.loads(json_section)
            return True, json_obj
        return False, None


    # parse node text to str by single regex
    def parse_to_str_by_regex(self, regex, nodeText='', sel=0):
        regValue = ''
        if not nodeText:
            nodeText = self.doc
        res = re.search(regex, nodeText, re.IGNORECASE)
        if res:
            regValue = res.group(sel)
        return regValue

    # parse nodetext by several regexs until find match
    def parse_to_str_by_regexs(self, regexs, nodeText='', sel=0):
        regValue = ''
        for regex in regexs:
            regValue = self.parse_to_str_by_regex(regex, nodeText, sel=sel)
            if regValue: break
        return regValue

    # auto determin regex or regexs
    def parse_to_str_by_r(self, regex, nodeText='', sel=0):
        regValue = ''
        if isinstance(regex, str):
            regValue = self.parse_to_str_by_regex(regex, nodeText, sel)
        elif isinstance(regex, list):
            regValue = self.parse_to_str_by_regexs(regex, nodeText, sel)
        return regValue

    def parse_to_multi_strs_by_regex(self, regex, nodeText=''):
        multivalue = []
        if not nodeText:
            nodeText = self.doc
        pattern = re.compile(regex, re.IGNORECASE)
        multiiters = pattern.finditer(nodeText)
        for it in multiiters:
            multivalue.append(it)
        return multivalue

    def parse_to_multi_strs_by_regexs(self, regexs, nodeText=''):
        multivalue = []
        for regex in regexs:
            mult = self.parse_to_multi_strs_by_regex(regex, nodeText)
            if mult:
                multivalue.extend(mult)
        return multivalue

    def parse_to_multi_strs_by_r(self, regexs, nodeText=''):
        multivalue = []
        if isinstance(regexs, str):
            multivalue = self.parse_to_multi_strs_by_regex(regexs, nodeText)
        elif isinstance(regexs, list):
            multivalue = self.parse_to_multi_strs_by_regexs(regexs, nodeText)
        return multivalue


        # parse decimal from regex

    def parse_to_decimal_by_regex(self, regex, decimal_str=r"(?:(\d{1,3}(\,\d{3})+)|(\d+))(\.\d{1,2})?", sel=0):
        value = 0
        decimalValue = self.parse_to_str_by_r(regex, sel=sel)
        if decimalValue:
            value = self.parse_to_decimal_from_str(decimalValue, decimal_str)
        return value

    def parse_to_decimal_by_regexs(self, regexs, decimal_str=r"(?:(\d{1,3}(\,\d{3})+)|(\d+))(\.\d{1,2})?", sel=0):
        value = 0
        for regex in regexs:
            value = self.parse_to_decimal_by_regex(regex, decimal_str, sel)
            if value > 0: break
        return value

    def parse_to_decimal_by_r(self, regexs, decimal_str=r"(?:(\d{1,3}(\,\d{3})+)|(\d+))(\.\d{1,2})?", sel=0):
        value = 0
        if isinstance(regexs, str):
            value = self.parse_to_decimal_by_regex(regexs, decimal_str, sel)
        elif isinstance(regexs, list):
            value = self.parse_to_decimal_by_regexs(regexs, decimal_str, sel)
        return value

    # parse decimal from str value

    def parse_to_decimal_from_str(self, strValue, decimal_rgx=r"(?:(\d{1,3}(\,\d{3})+)|(\d+))(\.\d{1,2})?", sel=0):
        res = re.search(decimal_rgx, strValue, re.IGNORECASE)
        if res:
            value = res.group(sel)
        else:
            value = 0
        try:
            value = float(str(value).replace(',', ''))
        except:
            value = 0
        return value


class XpathParser(Parser):

    def __init__(self, doc):
        super(XpathParser, self).__init__(doc)
        self.html_tree = lxml.html.fromstring(doc)

    def __text_deep(self,element,delimiter,default_value=" "):
        try:
            if delimiter == '' or delimiter == ' ':
                content = element.xpath('string()')
                if content : content = content.strip()
                return content
            children = element.xpath('.//text()')
            content = ' '
            for child in children:
                try:
                    text = str(child).strip()
                    if text[-1] == delimiter or text[0] == delimiter:
                        text = text.replace(delimiter, '')
                    if len(text) >= 1:
                        content = content + text.strip() + delimiter
                except:
                    pass
            if content is None or not content.strip():
                return default_value
            if content[-1] == delimiter:
                content = content[:-1]
            return content
        except:
            return default_value


    # parse value by xpath, if no node passed, use html tree as node (node must be an htmlelement)
    def parse_to_str_by_xpath(self, xpath, delimiter=' ', node=''):
        if isinstance(node, lxml.html.HtmlElement):
            targetNode = node.xpath(xpath)
        else:
            targetNode = self.html_tree.xpath(xpath)
        if targetNode and isinstance(targetNode[0], lxml.html.HtmlElement):
            targetValue = self.__text_deep(targetNode[0], delimiter)
        elif targetNode:
            targetValue = str(targetNode[0]).strip()
        else:
            targetValue = ''
        return targetValue

    # parse value by multi xpaths, loop xpath until find value otherwise, return ''
    def parse_to_str_by_xpaths(self, xpaths, delimiter=' ', node=''):
        targetValue = ''
        for path in xpaths:
            targetValue = self.parse_to_str_by_xpath(path, delimiter, node)
            if targetValue: break
        return targetValue


    def parse_to_str_by_x(self, xpath, delimiter='', node=''):
        targetValue = ''
        if isinstance(xpath, str):
            targetValue = self.parse_to_str_by_xpath(xpath, delimiter, node)
        elif isinstance(xpath, list):
            targetValue = self.parse_to_str_by_xpaths(xpath, delimiter, node)
        return targetValue

    # parse html by xpath fisrt, and then use regex to parse the str
    def parse_to_str_by_xr(self, regex, xpath, delimiter='', sel=0):
        regValue = ''
        xpathes = []
        if isinstance(xpath, str):
            xpathes.append(xpath)
        elif isinstance(xpath, list):
            xpathes = xpath
        for xp in xpathes:
            nodes = self.html_tree.xpath(xp)
            if nodes:
                for node in nodes:
                    nodeText = self.__text_deep(node, delimiter)
                    regValue = self.parse_to_str_by_r(regex, nodeText, sel)
                    if regValue:
                        break
                if regValue: break
        return regValue

    # parse html by xpath fisrt, and then use regex to parse the decimal
    def parse_to_decimal_by_xr(self, regex, xpath, delimiter='.', sel=0):
        value = 0
        decimalValue = self.parse_to_str_by_xr(regex, xpath, delimiter=delimiter, sel=sel)
        if decimalValue:
            if isinstance(decimalValue, float):
                return decimalValue
            elif isinstance(decimalValue, str):
                value = self.parse_to_decimal_from_str(decimalValue)
        return value

    # parse multi values from one xpath
    def parse_to_multi_strs_by_xpath(self, mxpath):
        multiValue = []
        attr = ''
        attrxpath = mxpath.split('/@')
        xpath = attrxpath[0]
        if len(attrxpath) > 1:
            attr = attrxpath[1]
        targetNode = self.html_tree.xpath(xpath)
        for childNode in targetNode:
            if attr:
                childValue = childNode.get(attr)
            else:
                childValue = self.__text_deep(childNode, ' ')
            multiValue.append(childValue)
        return multiValue

    def parse_to_multi_strs_by_xpaths(self, mxpaths):
        multiValues = []
        for mxpath in mxpaths:
            mv = self.parse_to_multi_strs_by_xpath(mxpath)
            if mv:
                multiValues.extend(mv)
        return multiValues

    def parse_to_multi_strs_by_x(self, mxpaths):
        multiValues = []
        if isinstance(mxpaths, str):
            multiValues = self.parse_to_multi_strs_by_xpath(mxpaths)
        elif isinstance(mxpaths, list):
            multiValues = self.parse_to_multi_strs_by_xpaths(mxpaths)
        return multiValues

    # parse multi values from a parent node
    def parse_to_strs_with_head(self, headXpath, bodyXpaths, delimiter=''):
        results = []
        headNode = self.html_tree.xpath(headXpath)
        for head in headNode:
            bodyValues = {}
            for key, bodyxpath in bodyXpaths.items():
                bodvalue = self.parse_to_str_by_x(bodyxpath, node=head, delimiter=delimiter)
                bodyValues[key] = bodvalue
            results.append(bodyValues)
        return results

    # parse to html form by xpath or xpaths
    def parse_to_html_by_x(self, xpath):
        htmlvalue = ''
        targetNode = []
        if isinstance(xpath, str):
            targetNode = self.html_tree.xpath(xpath)
        elif isinstance(xpath, list):
            for path in xpath:
                targetNode = self.html_tree.xpath(path)
                if targetNode: break
        if targetNode:
            htmlvalue = lxml.html.tostring(targetNode[0]).decode('utf8')
        return htmlvalue

    # parse decimal value from xpath,
    def parse_to_decimal_by_xpath(self, xpath, decimal_str=r"(?:(\d{1,3}(\,\d{3})+)|(\d+))(\.\d{1,2})?", sel=0):
        value = 0
        decimalValue = self.parse_to_str_by_xpath(xpath, '.')
        if decimalValue:
            if isinstance(decimalValue, float):
                return decimalValue
            value = self.parse_to_decimal_from_str(decimalValue, decimal_str, sel)
        return value

    # parse decimal value from xpaths
    def parse_to_decimal_by_xpaths(self, xpaths, decimal_str=r"(?:(\d{1,3}(\,\d{3})+)|(\d+))(\.\d{1,2})?", sel=0):
        value = 0
        for xpath in xpaths:
            value = self.parse_to_decimal_by_xpath(xpath, decimal_str, sel)
            if value > 0: break
        return value

    def parse_to_decimal_by_x(self, xpaths, decimal_str=r"(?:(\d{1,3}(\,\d{3})+)|(\d+))(\.\d{1,2})?", sel=0):
        value = 0
        if isinstance(xpaths, str):
            value = self.parse_to_decimal_by_xpath(xpaths, decimal_str, sel)
        elif isinstance(xpaths, list):
            value = self.parse_to_decimal_by_xpaths(xpaths, decimal_str, sel)
        return value


class XmlParser(Parser):

    def __init__(self, xml):
        super(XmlParser, self).__init__(xml)
        self.xmldoc = ET.fromstring(xml)
        self.ns = self.xmldoc.tag.split('}')[0] + '}'

    def __join_name_space(self, path, hasns):
        if hasns:
            full_path = path.format(self.ns)
        else:
            full_path = path
        return full_path

    def parse_text_by_path(self, path, parent_node='', hasns=True):
        target_value = ''
        node = self.parse_node_by_path(path, parent_node, hasns)
        if isinstance(node, ET.Element):
            target_value = node.text
        return target_value

    def parse_text_by_paths(self,paths, parent_node='',hasns=True):
        target_value = ''
        for path in paths:
            target_value = self.parse_text_by_path(path,parent_node,hasns)
            if target_value: break
        return target_value

    def parse_text_by_p(self,path, parent_node='', hasns=True):
        if isinstance(path, list):
            target_value = self.parse_text_by_paths(path,parent_node,hasns)
        else:
            target_value = self.parse_text_by_path(path, parent_node,hasns)
        return target_value

    def parse_decimal_by_path(self,path, parent_node='', hasns=True):
        decimal_value = 0
        text_value = self.parse_text_by_path(path, parent_node,hasns)
        if text_value:
            decimal_value = self.parse_to_decimal_from_str(text_value)
        return decimal_value

    def parse_decimal_by_paths(self,paths, parent_node='', hasns=True):
        decimal_value = 0
        for path in paths:
            decimal_value = self.parse_decimal_by_path(path,parent_node,hasns)
            if decimal_value != 0: break
        return decimal_value

    def parse_decimal_by_p(self,path, parent_node='', hasns=True):
        if isinstance(path, list):
            decimal_value = self.parse_decimal_by_paths(path,parent_node,hasns)
        else:
            decimal_value = self.parse_decimal_by_path(path, parent_node,hasns)
        return decimal_value



    def parse_all_text_by_path(self, path, parent_node='', hasns=True):
        node_text = []
        nodes = self.parse_all_nodes_by_path(path, parent_node, hasns)
        if nodes:
            for node in nodes:
                node_text.append(node.text)
        return node_text

    def parse_all_text_by_paths(self,paths,parent_node='', hasns=True):
        node_text=[]
        for path in paths:
            texts = self.parse_all_text_by_path(path, parent_node,hasns)
            if texts:
                node_text.extend(texts)
        return node_text

    def parse_all_text_by_p(self, path,parent_node='', hasns=True):
        if isinstance(path, list):
            list_value = self.parse_all_text_by_paths(path, parent_node, hasns)
        else:
            list_value = self.parse_all_text_by_path(path, parent_node,hasns)
        return list_value

    def parse_all_dict_by_path(self, path, parent_node='',hasns=True):
        node_dict = {}
        node = self.parse_node_by_path(path, parent_node,hasns)
        if node:
            for child_node in node:
                node_attrs = child_node.attrib
                node_attrs['Value'] = child_node.text
                node_dict[child_node.tag.split('}')[1]] = node_attrs
        return node_dict


    def parse_all_nodes_by_path(self, path, parent_node='', hasns=True):
        full_path = self.__join_name_space(path, hasns)
        if parent_node and isinstance(parent_node, ET.Element):
            nodes = parent_node.findall(full_path)
        else:
            nodes = self.xmldoc.findall(full_path)
        return nodes

    def parse_node_by_path(self, path, parent_node='', hasns=True):
        full_path = self.__join_name_space(path, hasns)
        if parent_node and isinstance(parent_node, ET.Element):
            node = parent_node.find(full_path)
        else:
            node = self.xmldoc.find(full_path)
        return node