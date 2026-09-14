from abc import ABC, abstractmethod


class BaseInferenceProvider(ABC):
    provider_name = "base-inference"

    @abstractmethod
    def infer(self, context):
        raise NotImplementedError
