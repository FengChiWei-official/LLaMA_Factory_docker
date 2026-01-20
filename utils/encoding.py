def detect_encoding(data: bytes) -> str:
	"""从字节数据中检测编码，并处理末尾截断（unexpected end of data）的情况。"""
	if not data:
		return 'utf-8'

	# 1. BOM 检查
	boms = [
		(b'\xff\xfe\x00\x00', 'utf-32-le'),
		(b'\x00\x00\xfe\xff', 'utf-32-be'),
		(b'\xff\xfe', 'utf-16-le'),
		(b'\xfe\xff', 'utf-16-be'),
		(b'\xef\xbb\xbf', 'utf-8-sig'),
	]
	for bom, enc in boms:
		if data.startswith(bom):
			return enc

	# 2. 尝试常见编码
	# 顺序很重要：utf-8 优先，然后是中文编码，最后是西文编码
	candidates = ('utf-8', 'gb18030', 'gbk', 'big5', 'iso-8859-1', 'cp1252')
	for enc in candidates:
		try:
			data.decode(enc)
			return enc
		except UnicodeDecodeError as e:
			# 如果报错是因为数据末尾截断（常见的 partial read 导致），
			# 则认为该编码是匹配的。
			if e.reason == 'unexpected end of data':
				return enc
			continue
	return 'latin1'


def switch_encoding(path: str, coding: str):
	"""自动检测给定文件的编码并转换为目标编码。

	参数:
		path: 要转换的文件路径。
		coding: 目标编码，例如 'utf-8', 'gb18030' 等。

	返回:
		(src_encoding, changed)
		src_encoding: 检测到的源编码（字符串）。
		changed: 布尔值，表示文件是否被修改（即源编码与目标编码不同）。

	实现细节/策略：
	- 先以二进制读取文件，检查常见 BOM（UTF-8/16/32）。
	- 若无 BOM，尝试按顺序用常见编码解码（utf-8, gb18030, gbk, big5, iso-8859-1, cp1252）。
	- 改进：支持检测被截断的 multi-byte 序列（如 utf-8 尾部字符不全）。
	- 若解码成功，则认为该编码为源编码；否则回退到 'latin1' 作为最终兜底（不会抛异常）。
	- 若源编码与目标编码等价（包括 utf-8 与 utf-8-sig 的简单归一化），则不修改文件并返回。
	- 写入是原子性的：先写入临时文件，再用 os.replace 覆盖原文件，保持权限不变。
	- 解码/编码在出错时使用 errors='replace' 做一次兜底，以避免破坏数据文件。
	"""
	import os

	# 读取原始二进制数据
	with open(path, 'rb') as f:
		data = f.read()

	src_enc = detect_encoding(data)

	# 归一化判断：使 utf-8 与 utf-8-sig 这类被视为等价
	def _norm(enc: str) -> str:
		if not enc:
			return ''
		return enc.replace('-', '').lower()

	if _norm(src_enc) == _norm(coding):
		return src_enc, False

	# 尝试用检测到的编码解码，失败时用 replace 兜底
	try:
		text = data.decode(src_enc)
	except Exception:
		try:
			text = data.decode(src_enc, errors='replace')
		except Exception:
			text = data.decode('latin1', errors='replace')

	# 原子性写回：写入临时文件再替换
	dirn = os.path.dirname(path) or '.'
	base = os.path.basename(path)
	tmp_path = os.path.join(dirn, base + '.tmp_encoding')

	# 保留原文件的权限与元数据（尽可能）
	try:
		st = os.stat(path)
		orig_mode = st.st_mode
	except Exception:
		orig_mode = None

	# 写入临时文件
	with open(tmp_path, 'wb') as wf:
		try:
			wf.write(text.encode(coding))
		except Exception:
			# 如果编码过程失败，用 replace 兜底再写一次
			wf.seek(0)
			wf.truncate(0)
			wf.write(text.encode(coding, errors='replace'))

	# 恢复权限并原子替换
	try:
		if orig_mode is not None:
			os.chmod(tmp_path, orig_mode)
	except Exception:
		pass

	os.replace(tmp_path, path)

	return src_enc, True


def switch_encoding_stream(path: str, coding: str, sample_size: int = 65536, chunk_size: int = 65536, errors: str = 'replace'):
	"""流式地将大文件从检测到的源编码转换为目标编码，避免一次性读入内存。

	参数:
		path: 文件路径
		coding: 目标编码
		sample_size: 用于检测编码的样本字节数
		chunk_size: 流式读取时每块的字节大小
		errors: 解码/编码错误处理策略（默认 'replace'）

	返回:
		(src_encoding, changed)
	"""
	import os
	import codecs

	# 读取样本并检测编码（使用统一的 detect_encoding 处理截断）
	with open(path, 'rb') as f:
		sample = f.read(sample_size)

	src_enc = detect_encoding(sample)

	def _norm(enc: str) -> str:
		if not enc:
			return ''
		return enc.replace('-', '').lower()

	if _norm(src_enc) == _norm(coding):
		return src_enc, False

	dirn = os.path.dirname(path) or '.'
	base = os.path.basename(path)
	tmp_path = os.path.join(dirn, base + '.tmp_encoding')

	# 保留权限
	try:
		st = os.stat(path)
		orig_mode = st.st_mode
	except Exception:
		orig_mode = None

	# 使用增量解码器/编码器逐块处理
	decoder = codecs.getincrementaldecoder(src_enc)(errors=errors)
	encoder = codecs.getincrementalencoder(coding)(errors=errors)

	with open(path, 'rb') as rf, open(tmp_path, 'wb') as wf:
		# 从头开始逐块读取
		while True:
			chunk = rf.read(chunk_size)
			if not chunk:
				break
			text = decoder.decode(chunk)
			if text:
				out = encoder.encode(text)
				if out:
					wf.write(out)

		# flush decoder -> get final text
		final_text = decoder.decode(b'', final=True)
		if final_text:
			wf.write(encoder.encode(final_text))

		# flush encoder final bytes if any
		try:
			tail = encoder.encode('', final=True)
			if tail:
				wf.write(tail)
		except TypeError:
			# 某些实现可能不支持 final arg; ignore
			pass

	try:
		if orig_mode is not None:
			os.chmod(tmp_path, orig_mode)
	except Exception:
		pass

	os.replace(tmp_path, path)

	return src_enc, True
