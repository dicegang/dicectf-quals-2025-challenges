function escapeHtml(x) {
  return x.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
}

export function escaped(strings, ...exps) {
  if (strings.length != exps.length + 1 || strings.length < 1) throw "invalid template usage"
  let result = [strings[0]]
  exps.forEach((exp, i) => result.push(escapeHtml(exp), strings[i + 1]))
  return result.join("")
}

export function html4(title, body) {
  let result = [`<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd"><HTML><HEAD>`]
  if (title !== null && title !== undefined) {
    result.push(`<TITLE>${escapeHtml(title)}</TITLE>`)
  }
  result.push(`</HEAD><BODY TEXT="white"><FONT FACE="Comic Sans MS">`)
  result.push(body)
  result.push(`</FONT></BODY></HTML>`)
  return result.join("")
}
