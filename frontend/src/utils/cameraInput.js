/**
 * 调用设备摄像头拍照（手机上唤起相机，桌面端退化为文件选择）
 * @param {(file: File) => void} onFile 选择完成后的回调
 * @param {'user' | 'environment'} facing 前置/后置摄像头
 */
export function capturePhoto(onFile, facing = 'user') {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'image/*'
  input.capture = facing
  input.style.display = 'none'
  input.addEventListener('change', () => {
    const file = input.files && input.files[0]
    if (file) onFile(file)
    input.remove()
  })
  document.body.appendChild(input)
  input.click()
}
