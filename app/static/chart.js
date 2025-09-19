(() => {
  const state = window.__LWC_STATE__ || {};
  const chartContainer = document.getElementById('chart');
  const emptyNotice = document.getElementById('empty');
  const errorBanner = document.getElementById('error-banner');
  const symbolInput = document.getElementById('symbol-input');
  const symbolDropdown = document.getElementById('symbol-dropdown');
  const symbolList = document.getElementById('symbol-list');
  const timeframeSelect = document.getElementById('timeframe-select');
  const timeframeWrapper = document.getElementById('timeframe-wrapper');
  const legendContainer = document.getElementById('legend');
  const legendOpen = document.getElementById('legend-open');
  const legendHigh = document.getElementById('legend-high');
  const legendLow = document.getElementById('legend-low');
  const legendClose = document.getElementById('legend-close');
  const legendChange = document.getElementById('legend-change');

  if (!chartContainer) {
    return;
  }

  if (!window.LightweightCharts) {
    showError('Failed to load charting library');
    return;
  }

  // Searchable Symbol Picker System
  class SymbolPicker {
    constructor(input, dropdown, list, symbols, onSelect) {
      this.input = input;
      this.dropdown = dropdown;
      this.list = list;
      this.symbols = symbols;
      this.onSelect = onSelect;
      this.filteredSymbols = [...symbols];
      this.selectedIndex = -1;
      this.isOpen = false;
      this.currentSymbol = symbols[0] || '';

      this.init();
    }

    init() {
      this.input.value = this.currentSymbol;
      this.setupEventListeners();
      this.renderSymbols();
    }

    setupEventListeners() {
      // Click on input to open/close
      this.input.addEventListener('click', (e) => {
        e.stopPropagation();
        if (this.isOpen) {
          this.close();
        } else {
          this.open();
        }
      });

      // Input events for search
      this.input.addEventListener('input', () => {
        this.filterSymbols(this.input.value);
      });

      // Keyboard navigation
      this.input.addEventListener('keydown', (e) => {
        this.handleKeydown(e);
      });

      // Click outside to close
      document.addEventListener('click', (e) => {
        if (!this.input.contains(e.target) && !this.dropdown.contains(e.target)) {
          this.close();
        }
      });

      // Focus events
      this.input.addEventListener('focus', () => {
        this.open();
      });

      this.input.addEventListener('blur', () => {
        // Delay to allow clicking on dropdown items
        setTimeout(() => {
          if (!this.dropdown.contains(document.activeElement)) {
            this.close();
          }
        }, 150);
      });
    }

    open() {
      this.isOpen = true;
      this.input.removeAttribute('readonly');
      this.dropdown.classList.add('show');
      this.selectedIndex = -1;
      this.filterSymbols(this.input.value);
    }

    close() {
      this.isOpen = false;
      this.input.setAttribute('readonly', 'true');
      this.dropdown.classList.remove('show');
      this.input.value = this.currentSymbol;
      this.selectedIndex = -1;
    }

    filterSymbols(query) {
      const searchTerm = query.toLowerCase();
      this.filteredSymbols = this.symbols.filter((symbol) =>
        symbol.toLowerCase().includes(searchTerm)
      );
      this.selectedIndex = -1;
      this.renderSymbols();
    }

    renderSymbols() {
      this.list.innerHTML = '';

      if (this.filteredSymbols.length === 0) {
        const noResults = document.createElement('div');
        noResults.className = 'symbol-item';
        noResults.textContent = 'No symbols found';
        noResults.style.color = '#9aa5b1';
        noResults.style.cursor = 'default';
        this.list.appendChild(noResults);
        return;
      }

      this.filteredSymbols.forEach((symbol, index) => {
        const item = document.createElement('div');
        item.className = 'symbol-item';
        item.dataset.symbol = symbol;
        item.dataset.index = index;

        // Highlight search matches
        const query = this.input.value.toLowerCase();
        if (query && symbol.toLowerCase().includes(query)) {
          const regex = new RegExp(`(${query})`, 'gi');
          item.innerHTML = symbol.replace(
            regex,
            '<span class="symbol-match">$1</span>'
          );
        } else {
          item.textContent = symbol;
        }

        if (symbol === this.currentSymbol) {
          item.classList.add('selected');
        }

        item.addEventListener('click', () => {
          this.selectSymbol(symbol);
        });

        this.list.appendChild(item);
      });
    }

    handleKeydown(e) {
      if (!this.isOpen) {
        if (e.key === 'Enter' || e.key === 'ArrowDown') {
          e.preventDefault();
          this.open();
        }
        return;
      }

      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          this.navigateDown();
          break;
        case 'ArrowUp':
          e.preventDefault();
          this.navigateUp();
          break;
        case 'Enter':
          e.preventDefault();
          if (this.selectedIndex >= 0 && this.filteredSymbols[this.selectedIndex]) {
            this.selectSymbol(this.filteredSymbols[this.selectedIndex]);
          }
          break;
        case 'Escape':
          e.preventDefault();
          this.close();
          break;
      }
    }

    navigateDown() {
      if (this.filteredSymbols.length === 0) {
        return;
      }

      this.selectedIndex = Math.min(
        this.selectedIndex + 1,
        this.filteredSymbols.length - 1
      );
      this.updateHighlight();
    }

    navigateUp() {
      if (this.filteredSymbols.length === 0) {
        return;
      }

      this.selectedIndex = Math.max(this.selectedIndex - 1, 0);
      this.updateHighlight();
    }

    updateHighlight() {
      const items = this.list.querySelectorAll('.symbol-item');
      items.forEach((item, index) => {
        item.classList.toggle('highlighted', index === this.selectedIndex);
      });

      // Scroll highlighted item into view
      if (this.selectedIndex >= 0 && items[this.selectedIndex]) {
        items[this.selectedIndex].scrollIntoView({
          block: 'nearest',
          behavior: 'smooth',
        });
      }
    }

    selectSymbol(symbol) {
      this.currentSymbol = symbol;
      this.input.value = symbol;
      this.close();
      if (this.onSelect) {
        this.onSelect(symbol);
      }
    }

    setValue(symbol) {
      if (this.symbols.includes(symbol)) {
        this.currentSymbol = symbol;
        this.input.value = symbol;
        this.renderSymbols();
      }
    }
  }

  // Bar Pattern Detection System
  class BarPatterns {
    static PATTERNS = {
      INSIDE_BAR: 'inside_bar',
      OUTSIDE_BAR: 'outside_bar',
    };

    static detectPattern(current, previous) {
      if (!previous) {
        return null;
      }

      // Inside Bar: Current high/low within previous high/low
      if (current.high <= previous.high && current.low >= previous.low) {
        return this.PATTERNS.INSIDE_BAR;
      }

      // Outside Bar: Current high/low exceed previous high/low
      if (current.high > previous.high && current.low < previous.low) {
        return this.PATTERNS.OUTSIDE_BAR;
      }

      return null;
    }

    static applyPatternColors(candleData) {
      const patternsFound = { inside: 0, outside: 0 };

      const result = candleData.map((candle, index) => {
        if (index === 0) {
          return candle;
        }

        const current = candle;
        const previous = candleData[index - 1];
        const pattern = this.detectPattern(current, previous);

        if (pattern) {
          if (pattern === this.PATTERNS.INSIDE_BAR) {
            patternsFound.inside++;
            const isBullish = current.close >= current.open;
            return {
              ...current,
              color: 'white',
              wickColor: isBullish ? '#26a69a' : '#ef5350',
            };
          }

          if (pattern === this.PATTERNS.OUTSIDE_BAR) {
            patternsFound.outside++;
            const isBullish = current.close >= current.open;
            return {
              ...current,
              color: 'yellow',
              wickColor: isBullish ? '#26a69a' : '#ef5350',
            };
          }
        }

        return candle;
      });

      return result;
    }
  }

  function showError(message) {
    errorBanner.textContent = message;
    errorBanner.style.display = 'block';
  }

  function hideError() {
    errorBanner.style.display = 'none';
  }

  function showEmpty(message = 'No data for the selected inputs.') {
    emptyNotice.textContent = message;
    emptyNotice.style.display = 'block';
  }

  function hideEmpty() {
    emptyNotice.style.display = 'none';
  }

  // Handle initial state errors
  if (state.error) {
    showError(state.error);
  }

  if (!state.symbols || state.symbols.length === 0) {
    showEmpty('No symbols available. Ensure the dataset is populated.');
    return;
  }

  // Initialize symbol picker
  let symbolPickerInstance;
  let currentSymbol = state.activeSymbol || state.symbols[0];

  const initSymbolPicker = () => {
    symbolPickerInstance = new SymbolPicker(
      symbolInput,
      symbolDropdown,
      symbolList,
      state.symbols,
      (selectedSymbol) => {
        currentSymbol = selectedSymbol;
        loadData();
      }
    );

    // Set initial symbol
    symbolPickerInstance.setValue(currentSymbol);
  };

  initSymbolPicker();

  if (!state.timeframes || state.timeframes.length === 0) {
    timeframeWrapper.style.display = 'none';
  } else {
    state.timeframes.forEach((tf) => {
      const option = document.createElement('option');
      option.value = tf;
      option.textContent = tf;
      timeframeSelect.appendChild(option);
    });
    timeframeSelect.value = state.activeTimeframe || state.timeframes[0];
  }

  let currentTimeframe =
    state.timeframes && state.timeframes.length ? timeframeSelect.value || null : null;

  // Create chart using v5.0.8 API
  const chart = window.LightweightCharts.createChart(chartContainer, {
    layout: {
      background: { color: '#11161c' },
      textColor: '#d8dee9',
    },
    width: chartContainer.clientWidth,
    height: chartContainer.clientHeight,
    grid: {
      horzLines: { color: '#1f2933' },
      vertLines: { color: '#1f2933' },
    },
    crosshair: { mode: window.LightweightCharts.CrosshairMode.Normal },
    rightPriceScale: { borderVisible: false },
    timeScale: { borderVisible: false },
  });

  const candleSeries = chart.addSeries(window.LightweightCharts.CandlestickSeries, {
    upColor: '#26a69a',
    downColor: '#ef5350',
    borderUpColor: '#26a69a',
    borderDownColor: '#ef5350',
    wickUpColor: '#26a69a',
    wickDownColor: '#ef5350',
  });

  // Legend update functionality
  let lastBar = null;
  let previousBar = null;

  function updateLegend(bar, previousBar) {
    if (!bar || !legendContainer) {
      return;
    }

    legendOpen.textContent = bar.open.toFixed(4);
    legendHigh.textContent = bar.high.toFixed(4);
    legendLow.textContent = bar.low.toFixed(4);
    legendClose.textContent = bar.close.toFixed(4);

    // Calculate numerical and percentage change relative to previous open
    if (previousBar) {
      const numericalChange = bar.close - previousBar.open;
      const percentageChange = (numericalChange / previousBar.open) * 100;
      const changeText = `${numericalChange >= 0 ? '+' : ''}${numericalChange.toFixed(4)} (${percentageChange >= 0 ? '+' : ''}${percentageChange.toFixed(2)}%)`;
      legendChange.textContent = changeText;
      legendChange.className = `legend-value legend-change ${numericalChange >= 0 ? 'positive' : 'negative'}`;
    } else {
      legendChange.textContent = '-';
      legendChange.className = 'legend-value legend-change';
    }

    legendContainer.style.display = 'block';
  }

  function hideLegend() {
    if (legendContainer) {
      legendContainer.style.display = 'none';
    }
  }

  // Subscribe to crosshair position changes for legend updates
  chart.subscribeCrosshairMove((param) => {
    if (!param.time || !param.seriesData || !param.seriesData.has(candleSeries)) {
      // Show last bar when no crosshair position
      if (lastBar && previousBar) {
        updateLegend(lastBar, previousBar);
      } else {
        hideLegend();
      }
      return;
    }

    const bar = param.seriesData.get(candleSeries);
    if (bar) {
      // Find the previous bar for percentage calculation
      const barTime = param.time;
      const allData = candleSeries.data();
      const currentIndex = allData.findIndex((d) => d.time === barTime);
      const prevBar = currentIndex > 0 ? allData[currentIndex - 1] : null;
      updateLegend(bar, prevBar);
    }
  });

  // Handle window resize
  window.addEventListener('resize', () => {
    chart.applyOptions({
      width: chartContainer.clientWidth,
      height: chartContainer.clientHeight,
    });
  });

  // Event listeners

  if (state.timeframes && state.timeframes.length) {
    timeframeSelect.addEventListener('change', () => {
      currentTimeframe = timeframeSelect.value;
      loadData();
    });
  }

  async function loadData() {
    try {
      const params = new URLSearchParams({ symbol: currentSymbol });
      if (currentTimeframe) {
        params.append('timeframe', currentTimeframe);
      }
      // Only add limit parameter if it's > 0 (0 means unlimited)
      const limitValue = state.limit || 0;
      if (limitValue > 0) {
        params.append('limit', limitValue);
      }

      const response = await fetch(`/ohlc?${params.toString()}`);
      if (!response.ok) {
        const message = await response.text();
        showError(`Failed to load data: ${message}`);
        return;
      }

      const rows = await response.json();

      if (!rows.length) {
        showEmpty();
        candleSeries.setData([]);
        return;
      }

      hideEmpty();
      hideError();

      const candleData = rows.map((row) => {
        const time = Math.floor(new Date(row.time).getTime() / 1000);
        return {
          time,
          open: parseFloat(row.open),
          high: parseFloat(row.high),
          low: parseFloat(row.low),
          close: parseFloat(row.close),
        };
      });

      const finalCandleData = BarPatterns.applyPatternColors(candleData);

      candleSeries.setData(finalCandleData);
      chart.timeScale().fitContent();

      // Update legend with last bar data
      if (finalCandleData.length > 0) {
        lastBar = finalCandleData[finalCandleData.length - 1];
        previousBar =
          finalCandleData.length > 1
            ? finalCandleData[finalCandleData.length - 2]
            : null;
        updateLegend(lastBar, previousBar);
      }
    } catch (error) {
      showError(`Error loading data: ${error.message}`);
    }
  }

  loadData();
})();
