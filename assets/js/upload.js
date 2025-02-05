(
    () => {
        const selector = '[data-upload-field]'
        const getDraggable = (e) => e.target.matches(selector) ? e.target : e.target.closest(selector)
        const approve = (container, file) => {
            if (typeof (file) === 'undefined') {
                return false
            }

            const fileInput = container.querySelector('input[type="file"]')
            const accepts = fileInput.getAttribute('accept')
            const validTypes = []

            if (accepts) {
                accepts.split(',').forEach(
                    (contentType) => {
                        const regex = new RegExp('^' + contentType.replace('.', '\\.').replace('*', '.*') + '$')

                        if (file.type.match(regex)) {
                            validTypes.push(file.type)
                        }
                    }
                )
            }

            if (!validTypes.length) {
                alert('The selected file is not of a type supported by this field.')
                return false
            }

            return true
        }

        const showUpload = (container, file) => {
            const card = container.querySelector('.widget-contents')
            const originalHTML = card.innerHTML
            const btn = document.createElement('button')
            const fileInput = container.querySelector('input[type="file"]')
            const size = Math.round(file.size / 1024)

            card.innerHTML = `<p class="lead fw-normal mb-0"><i class="bi bi-file-earmark-music-fill"></i> ${file.name}</p><p>${size.toLocaleString()}kb</p>`
            btn.addEventListener('click',
                () => {
                    card.innerHTML = originalHTML
                    fileInput.value = ''
                }
            )

            btn.classList.add('btn')
            btn.classList.add('btn-outline-secondary')
            btn.type = 'button'
            btn.innerText = 'Replace file'
            card.appendChild(btn)
        }

        const handleDragenter = (e) => {
            const draggable = getDraggable(e)

            if (!draggable) {
                return
            }

            if (!draggable.classList.contains('active')) {
                draggable.classList.add('active')
            }
        }

        const handleDragover = (e) => {
            e.stopPropagation()
            e.preventDefault()

            e.dataTransfer.dropEffect = 'copy'
        }

        const handleDragleave = (e) => {
            const draggable = getDraggable(e)

            if (!draggable) {
                return
            }

            draggable.classList.remove('active')
        }

        const handleDrop = (e) => {
            e.stopPropagation()
            e.preventDefault()

            const draggable = getDraggable(e)
            const fileInput = draggable.querySelector('input[type="file"]')

            if (!draggable) {
                return
            }

            draggable.classList.remove('active')
            const files = e.dataTransfer.files

            if (files.length > 0) {
                if (approve(draggable, files[0])) {
                    fileInput.files = files
                    showUpload(draggable, files[0])
                }
            }
        }

        const handleClick = (e) => {
            const btnSelector = `${selector} [data-pr-action="browse"]`
            const btn = e.target.matches(btnSelector) ? e.target : e.target.closest(btnSelector)

            if (!btn) {
                return
            }

            const field = e.target.closest(selector).querySelector('input[type="file"]')
            e.preventDefault()
            
            if (field) {
                field.click()
            }
        }

        const handleChange = (e) => {
            const inputSelector = `${selector} input[type="file"]`
            const input = e.target.matches(inputSelector) ? e.target : e.target.closest(inputSelector)

            if (!input) {
                return
            }

            const container = input.closest(selector)
            showUpload(container, input.files[0])
        }

        const provision = (container) => {
            container.addEventListener('dragenter', handleDragenter, false)
            container.addEventListener('dragover', handleDragover, false)
            container.addEventListener('dragleave', handleDragleave, false)
            container.addEventListener('drop', handleDrop, false)
            container.addEventListener('click', handleClick, false)
            container.addEventListener('change', handleChange, false)
        }

        document.querySelectorAll(selector).forEach(provision)
        document.addEventListener(
            'pr.modal.mount',
            (e) => e.target.querySelectorAll(selector).forEach(provision),
            true
        )
    }
)()
