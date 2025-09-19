(() => {
  const state = window.__LWC_STATE__ || {};
  const chartContainer = document.getElementById('chart');
  const emptyNotice = document.getElementById('empty');
  const errorBanner = document.getElementById('error-banner');
  const symbolSelect = document.getElementById('symbol-select');
  const timeframeSelect = document.getElementById('timeframe-select');
  const timeframeWrapper = document.getElementById('timeframe-wrapper');
  const patternToggle = document.getElementById('pattern-toggle');

  if (!chartContainer) {
    return;
  }

  if (!window.LightweightCharts) {
    showError('Failed to load charting library');
    return;
  }

  // Bar Pattern Detection System
  class BarPatterns {
    static PATTERNS = {
      INSIDE_BAR: 'inside_bar',
      OUTSIDE_BAR: 'outside_bar',
    };

    static detectPattern(current, previous) {
      if (!previous) return null;

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
      let patternsFound = { inside: 0, outside: 0 };

      const result = candleData.map((candle, index) => {
        if (index === 0) return candle;

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
              wickColor: isBullish ? '#26a69a' : '#ef5350'
            };
          }

          if (pattern === this.PATTERNS.OUTSIDE_BAR) {
            patternsFound.outside++;
            const isBullish = current.close >= current.open;
            return {
              ...current,
              color: 'yellow',
              wickColor: isBullish ? '#26a69a' : '#ef5350'
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

  // Populate dropdowns
  state.symbols.forEach((symbol) => {
    const option = document.createElement('option');
    option.value = symbol;
    option.textContent = symbol;
    symbolSelect.appendChild(option);
  });
  symbolSelect.value = state.activeSymbol || state.symbols[0];

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

  let currentSymbol = symbolSelect.value;
  let currentTimeframe = state.timeframes && state.timeframes.length
    ? timeframeSelect.value || null
    : null;

  // Create chart using v5.0.8 API
  const chart = window.LightweightCharts.createChart(chartContainer, {
    layout: {
      background: { color: '#11161c' },
      textColor: '#d8dee9'
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

  // Handle window resize
  window.addEventListener('resize', () => {
    chart.applyOptions({
      width: chartContainer.clientWidth,
      height: chartContainer.clientHeight,
    });
  });

  // Event listeners
  symbolSelect.addEventListener('change', () => {
    currentSymbol = symbolSelect.value;
    loadData();
  });

  if (state.timeframes && state.timeframes.length) {
    timeframeSelect.addEventListener('change', () => {
      currentTimeframe = timeframeSelect.value;
      loadData();
    });
  }

  patternToggle.addEventListener('change', () => {
    loadData();
  });

  async function loadData() {
    try {

      const params = new URLSearchParams({ symbol: currentSymbol });
      if (currentTimeframe) {
        params.append('timeframe', currentTimeframe);
      }
      params.append('limit', state.limit || 500);

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

      const finalCandleData = patternToggle.checked
        ? BarPatterns.applyPatternColors(candleData)
        : candleData;

      candleSeries.setData(finalCandleData);
      chart.timeScale().fitContent();

    } catch (error) {
      showError(`Error loading data: ${error.message}`);
    }
  }

  loadData();
})();