(
    () => {
        const search = async (term) => {
            if (!term) {
                return []
            }

            const response = await fetch(
                'https://itunes.apple.com/search?' + new URLSearchParams(
                    {
                        term: term,
                        media: 'podcast',
                        entity: 'podcast',
                        limit: 10,
                        lang: 'en_us'
                    }
                ).toString()
            )

            if (response.ok) {
                const json = await response.json()

                return json.results.filter(
                    (result) => result.kind === 'podcast'
                ).map(
                    (result) => {
                        return {
                            id: result.trackId,
                            artwork: result.artworkUrl100,
                            name: result.trackName
                        }
                    }
                )
            }

            console.warn(response)
            return []
        }

        const lookup = async (id) => {
            if (!id) {
                return
            }

            const response = await fetch(
                'https://itunes.apple.com/lookup?' + new URLSearchParams(
                    {
                        id: id
                    }
                ).toString()
            )

            if (response.ok) {
                const json = await response.json()
                const items = json.results.filter(
                    (result) => result.kind === 'podcast'
                ).map(
                    (result) => {
                        return {
                            id: result.trackId,
                            artwork: result.artworkUrl100,
                            name: result.trackName
                        }
                    }
                )

                return items.length ? items[0] : null
            }

            console.warn(response)
            return []
        }

        const debounce = (func) => {
            if (!timer) {
                timer = setTimeout(
                    async () => {
                        if (debounced) {
                            await debounced()
                        }

                        timer = null
                    },
                    500
                )

                return
            }

            debounced = func
        }

        const activateUp = () => {
            const container = document.querySelector('input[data-pr-source="itunes"]').parentNode
            const elements = container.querySelectorAll(`[data-pr-item]`)
            const count = elements.length
            let found = false

            elements.forEach(
                (el, i) => {
                    if (found) {
                        return
                    }

                    if (el.classList.contains('active')) {
                        el.classList.remove('active')

                        if (i === 0) {
                            return
                        }

                        elements[i - 1].classList.add('active')
                        found = true
                    }
                }
            )

            if (!found && count) {
                elements[count - 1].classList.add('active')
            }
        }

        const activateDown = () => {
            const container = document.querySelector('input[data-pr-source="itunes"]').parentNode
            const elements = container.querySelectorAll(`[data-pr-item]`)
            const count = elements.length
            let found = false

            elements.forEach(
                (el, i) => {
                    if (found) {
                        return
                    }

                    if (el.classList.contains('active')) {
                        el.classList.remove('active')

                        if (i >= count - 1) {
                            return
                        }

                        elements[i + 1].classList.add('active')
                        found = true
                    }
                }
            )

            if (!found && elements.length) {
                elements[0].classList.add('active')
            }
        }

        const activate = (item) => {
            const container = document.querySelector('input[data-pr-source="itunes"]').parentNode

            container.querySelectorAll(`[data-pr-item].active`).forEach(
                (el) => {
                    el.classList.remove('active')
                }
            )

            container.querySelectorAll(`[data-pr-item="${item.id}"]`).forEach(
                (el) => {
                    el.classList.add('active')
                }
            )
        }

        const select = () => {
            const container = document.querySelector('input[data-pr-source="itunes"]').parentNode

            container.querySelectorAll(`[data-pr-item].active`).forEach(
                (el) => {
                    el.dispatchEvent(
                        new CustomEvent('pr.search.select')
                    )
                }
            )
        }

        const display = (data) => {
            const input = document.querySelector('input[data-pr-source="itunes"]')
            const container = input.parentNode
            const name = input.getAttribute('data-pr-name')
            
            container.querySelectorAll(`input[name="${name}"]`).forEach(
                (hiddenInput) => {
                    hiddenInput.value = ''
                }
            )

            container.querySelectorAll('[data-pr-search]').forEach(
                (el) => {
                    el.parentNode.removeChild(el)
                }
            )

            const listNode = document.createElement('div')

            listNode.setAttribute('data-pr-search', true)
            listNode.classList.add('list-group')

            data.forEach(
                (item) => {
                    const itemNode = document.createElement('a')
                    const containerNode = document.createElement('div')
                    const imgNode = document.createElement('img')
                    const textNode = document.createElement('span')

                    containerNode.classList.add('d-flex')
                    containerNode.classList.add('align-items-center')

                    itemNode.href = 'javascript:;'
                    itemNode.setAttribute('data-pr-item', item.id)
                    itemNode.classList.add('list-group-item')
                    itemNode.classList.add('list-group-item-action')
                    itemNode.classList.add('d-block')
                    itemNode.addEventListener('click',
                        (e) => {
                            e.preventDefault()
                            activate(item)
                            select()
                        }
                    )

                    itemNode.addEventListener('pr.search.select',
                        (e) => {
                            container.querySelectorAll('input[data-pr-source="itunes"]').forEach(
                                (input) => {
                                    input.value = item.name

                                    const name = input.getAttribute('data-pr-name')
                                    input.parentNode.querySelectorAll(`input[name="${name}"]`).forEach(
                                        (hiddenInput) => {
                                            display([])
                                            hiddenInput.value = item.id
                                        }
                                    )
                                }
                            )
                        }
                    )

                    imgNode.src = item.artwork
                    imgNode.width = 50
                    imgNode.classList.add('me-2')

                    textNode.innerText = item.name

                    containerNode.appendChild(imgNode)
                    containerNode.appendChild(textNode)
                    itemNode.appendChild(containerNode)
                    listNode.appendChild(itemNode)
                }
            )

            container.appendChild(listNode)
        }

        let timer = null
        let debounced = null

        document.body.addEventListener('input',
            (e) => {
                const selector = 'input[data-pr-source="itunes"]'
                const input = e.target.matches(selector) ? e.target : e.target.closest(selector)

                if (!input) {
                    return
                }

                debounce(
                    async () => {
                        const results = await search(input.value)

                        display(results)
                    }
                )
            },
            false
        )

        document.body.addEventListener('paste',
            (e) => {
                const selector = 'input[data-pr-source="itunes"]'
                const input = e.target.matches(selector) ? e.target : e.target.closest(selector)

                if (!input) {
                    return
                }

                debounce(
                    async () => {
                        const results = await search(input.value)

                        display(results)
                    }
                )
            },
            false
        )

        document.body.addEventListener('keydown',
            (e) => {
                const selector = 'input[data-pr-source="itunes"]'
                const input = e.target.matches(selector) ? e.target : e.target.querySelector(selector)

                if (!input) {
                    return
                }

                const name = input.getAttribute('data-pr-name')
                const hiddenInput = input.parentNode.querySelector(`input[name="${name}"]`)

                switch (e.keyCode) {
                    case 38:
                        activateUp()
                        e.preventDefault()
                        break

                    case 40:
                        activateDown()
                        e.preventDefault()
                        break

                    case 13:
                        if (hiddenInput && hiddenInput.value && !isNaN(parseInt(hiddenInput.value))) {
                            return
                        }

                        select()
                        e.preventDefault()
                }
            }
        )

        const provision = (input) => {
            const hiddenInput = document.createElement('input')

            hiddenInput.name = input.name
            input.novalidate = true
            hiddenInput.type = 'hidden'
            hiddenInput.value = input.value

            input.setAttribute('data-pr-name', input.name)
            input.removeAttribute('name')
            input.parentNode.appendChild(hiddenInput)

            if (input.value && !isNaN(parseInt(input.value))) {
                input.disabled = true

                lookup(input.value).then(
                    (result) => {
                        if (!result) {
                            return
                        }

                        input.value = result.name
                        hiddenInput.value = result.id
                        input.disabled = false
                    }
                )

                input.valueu = ''
            }
        }

        document.querySelectorAll('input[data-pr-source="itunes"]').forEach(provision)
        document.addEventListener(
            'pr.modal.mount',
            (e) => e.target.querySelectorAll('input[data-pr-source="itunes"]').forEach(provision),
            true
        )
    }
)()
